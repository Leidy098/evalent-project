from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import Interview, Message, Score
from .forms import InterviewForm
from ai_agent.service import generate_ai_response
import json
import base64

from reports.utils import compute_scores, plot_promedios, plot_comparativa, plot_radar, plot_pie_strengths


@login_required
def interview_list(request):
    interviews = Interview.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "interviews/list.html", {"interviews": interviews})


@login_required
def interview_create(request):
    if request.method == "POST":
        form = InterviewForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.user = request.user
            interview.save()

            result = generate_ai_response(interview, "")
            question = result.get("question")
            feedback = result.get("feedback")
            scores = result.get("scores")

            if question:
                ai_msg = Message.objects.create(interview=interview, role="ai", content=question)
                if scores:
                    Score.objects.create(
                        message=ai_msg,
                        claridad=scores.get("claridad", 0),
                        confianza=scores.get("confianza", 0),
                        contenido=scores.get("contenido", 0),
                        creatividad=scores.get("creatividad", 0),
                        lenguaje=scores.get("lenguaje", 0),
                    )
            if feedback:
                Message.objects.create(interview=interview, role="feedback", content=feedback)

            interview.asked_questions += 1
            interview.save()
            return redirect("interviews:interview_detail", pk=interview.pk)
    else:
        form = InterviewForm()
    return render(request, "interviews/create.html", {"form": form})


@login_required
def interview_detail(request, pk):
    interview = get_object_or_404(Interview, pk=pk, user=request.user)

    if interview.is_finished:
        return redirect("interviews:interview_results", pk=interview.pk)

    messages_list = interview.messages.order_by("timestamp")

    if request.method == "POST":
        if "finish" in request.POST:
            interview.is_finished = True
            interview.save()
            return redirect("interviews:interview_results", pk=interview.pk)

        user_answer = request.POST.get("answer")
        if user_answer:
            Message.objects.create(interview=interview, role="user", content=user_answer)

        result = generate_ai_response(interview, user_answer or "")
        question = result.get("question")
        feedback = result.get("feedback")
        scores = result.get("scores")

        if question:
            ai_msg = Message.objects.create(interview=interview, role="ai", content=question)
            if scores:
                Score.objects.create(
                    message=ai_msg,
                    claridad=scores.get("claridad", 0),
                    confianza=scores.get("confianza", 0),
                    contenido=scores.get("contenido", 0),
                    creatividad=scores.get("creatividad", 0),
                    lenguaje=scores.get("lenguaje", 0),
                )
        if feedback:
            Message.objects.create(interview=interview, role="feedback", content=feedback)

        interview.asked_questions += 1

        if interview.mode == "questions" and interview.max_questions and interview.asked_questions >= interview.max_questions:
            interview.is_finished = True
        elif interview.mode == "time" and interview.time_limit:
            elapsed = (timezone.now() - interview.created_at).total_seconds() / 60
            if elapsed >= interview.time_limit:
                interview.is_finished = True

        interview.save()

        if interview.is_finished:
            return redirect("interviews:interview_results", pk=interview.pk)

        return redirect("interviews:interview_detail", pk=interview.pk)

    return render(request, "interviews/detail.html", {"interview": interview, "messages": messages_list})


@login_required
@csrf_exempt
def transcribe_audio(request, pk):
    """Endpoint para transcribir audio"""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    try:
        interview = get_object_or_404(Interview, pk=pk, user=request.user)
        data = json.loads(request.body)
        audio_base64 = data.get("audio")
        
        if not audio_base64:
            return JsonResponse({"error": "No se recibió audio"}, status=400)
        
        from ai_agent.voice_utils import transcribe_audio as transcribe
        
        transcribed_text = transcribe(audio_base64)
        
        if transcribed_text:
            return JsonResponse({"text": transcribed_text})
        else:
            return JsonResponse({"error": "Error al transcribir"}, status=500)
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@csrf_exempt
def generate_voice_response(request, pk):
    """Endpoint para generar respuesta con voz"""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    try:
        interview = get_object_or_404(Interview, pk=pk, user=request.user)
        data = json.loads(request.body)
        user_message = data.get("message", "")
        
        if user_message:
            Message.objects.create(interview=interview, role="user", content=user_message)
        
        result = generate_ai_response(interview, user_message)
        question = result.get("question")
        feedback = result.get("feedback")
        scores = result.get("scores")
        
        ai_msg_id = None
        if question:
            ai_msg = Message.objects.create(interview=interview, role="ai", content=question)
            ai_msg_id = ai_msg.id
            if scores:
                Score.objects.create(
                    message=ai_msg,
                    claridad=scores.get("claridad", 0),
                    confianza=scores.get("confianza", 0),
                    contenido=scores.get("contenido", 0),
                    creatividad=scores.get("creatividad", 0),
                    lenguaje=scores.get("lenguaje", 0),
                )
        
        if feedback:
            Message.objects.create(interview=interview, role="feedback", content=feedback)
        
        interview.asked_questions += 1
        
        should_finish = False
        if interview.mode == "questions" and interview.max_questions:
            if interview.asked_questions >= interview.max_questions:
                should_finish = True
        elif interview.mode == "time" and interview.time_limit:
            elapsed = (timezone.now() - interview.created_at).total_seconds() / 60
            if elapsed >= interview.time_limit:
                should_finish = True
        
        if should_finish:
            interview.is_finished = True
        
        interview.save()
        
        audio_base64 = None
        try:
            from ai_agent.voice_utils import text_to_speech_edge_tts
            if question:
                audio_bytes = text_to_speech_edge_tts(question, interview.language)
                if audio_bytes:
                    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error generando audio: {e}")
        
        return JsonResponse({
            "question": question,
            "feedback": feedback,
            "scores": scores,
            "audio": audio_base64,
            "is_finished": should_finish,
            "message_id": ai_msg_id
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def interview_finish(request, pk):
    interview = get_object_or_404(Interview, pk=pk, user=request.user)
    interview.is_finished = True
    interview.save()
    return JsonResponse({"status": "ok"})


@login_required
def interview_delete(request, pk):
    interview = get_object_or_404(Interview, pk=pk, user=request.user)
    interview.delete()
    messages.success(request, "La entrevista fue eliminada correctamente.")
    return redirect("interviews:interview_list")


@login_required
def interview_results(request, pk):
    interview = get_object_or_404(Interview, pk=pk, user=request.user)

    scores = [msg.score for msg in interview.messages.all() if hasattr(msg, "score")]
    if scores:
        promedio = {
            "claridad": sum(s.claridad for s in scores) / len(scores),
            "confianza": sum(s.confianza for s in scores) / len(scores),
            "contenido": sum(s.contenido for s in scores) / len(scores),
            "creatividad": sum(s.creatividad for s in scores) / len(scores),
            "lenguaje": sum(s.lenguaje for s in scores) / len(scores),
        }
    else:
        promedio = {"claridad": 0, "confianza": 0, "contenido": 0, "creatividad": 0, "lenguaje": 0}

    puntaje = int(sum(promedio.values()) / 5)

    context = {
        "interview": interview,
        "puntaje": puntaje,
        "total_preguntas": interview.asked_questions,
        "comparativa": [60, 75, puntaje],
        "promedio": promedio,
    }
    return render(request, "interviews/results.html", context)


@login_required
def interview_export_pdf(request, pk):
    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from datetime import datetime

    interview = get_object_or_404(Interview, pk=pk, user=request.user)
    promedio, puntaje, comparativa = compute_scores(interview)
    png_promedios = plot_promedios(promedio)
    png_comp = plot_comparativa(comparativa)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=70, bottomMargin=60)
    styles = getSampleStyleSheet()
    Story = []

    Story.append(Paragraph("<b>Reporte de Entrevista – Evalent</b>", styles["Title"]))
    Story.append(Spacer(1, 10))

    line = Table([[""]], colWidths=[450])
    line.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 2, colors.HexColor("#0d6efd"))]))
    Story.append(line)
    Story.append(Spacer(1, 12))

    meta = f"""
    <b>Usuario:</b> {request.user.username}<br/>
    <b>Cargo:</b> {interview.position}<br/>
    <b>Tipo de entrevista:</b> {interview.get_interview_type_display()}<br/>
    <b>Nivel:</b> {interview.get_level_display()}<br/>
    <b>Idioma:</b> {interview.get_language_display()}<br/>
    <b>Modo:</b> {interview.get_mode_display()}<br/>
    <b>Puntaje final:</b> {puntaje}/100<br/>
    <b>Preguntas respondidas:</b> {interview.asked_questions}<br/>
    <b>Fecha:</b> {interview.created_at.strftime("%d/%m/%Y %H:%M")}
    """
    Story.append(Paragraph(meta, styles["Normal"]))
    Story.append(Spacer(1, 20))

    data = [["Criterio", "Puntaje"]] + [[k.capitalize(), f"{v:.1f}"] for k, v in promedio.items()]
    table = Table(data, hAlign="LEFT", colWidths=[200, 80])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ]))
    Story.append(table)
    Story.append(Spacer(1, 20))

    Story.append(Paragraph("<b>Gráfico 1:</b> Promedio por criterio", styles["Heading3"]))
    Story.append(Image(png_promedios, width=400, height=250))
    Story.append(Spacer(1, 16))

    Story.append(Paragraph("<b>Gráfico 2:</b> Comparativa de desempeño", styles["Heading3"]))
    Story.append(Image(png_comp, width=400, height=250))
    Story.append(Spacer(1, 20))

    Story.append(Paragraph("<b>Gráfico 3:</b> Radar de Desempeño", styles["Heading3"]))
    Story.append(Image(plot_radar(promedio), width=400, height=350))
    Story.append(Spacer(1, 20))

    Story.append(Paragraph("<b>Gráfico 4:</b> Fortalezas vs Debilidades", styles["Heading3"]))
    Story.append(Image(plot_pie_strengths(promedio), width=400, height=300))
    Story.append(Spacer(1, 20))

    Story.append(PageBreak())
    Story.append(Paragraph("<b>Consejos destacados de la IA</b>", styles["Heading2"]))
    Story.append(Spacer(1, 12))

    feedback_msgs = [m.content for m in interview.messages.all() if m.role == "feedback"]
    if feedback_msgs:
        for i, msg in enumerate(feedback_msgs, 1):
            Story.append(Paragraph(f"{i}. {msg}", styles["Normal"]))
            Story.append(Spacer(1, 8))
    else:
        Story.append(Paragraph("No se generaron consejos en esta entrevista.", styles["Italic"]))

    Story.append(Spacer(1, 30))
    Story.append(Paragraph(
        f"<b>Generado por Evalent</b> — {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>"
        "Simulador de entrevistas con IA.",
        ParagraphStyle("footer", fontSize=9, textColor=colors.grey),
    ))

    doc.build(Story)
    pdf_value = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_value, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="reporte_entrevista_{interview.pk}.pdf"'
    return response