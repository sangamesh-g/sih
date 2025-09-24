from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .ge import analyze_civic_issue
import tempfile

@csrf_exempt
def analyze_report(request):
    if request.method == "POST":
        user_text = request.POST.get("text")
        image_file = request.FILES.get("image")

        # Save temporarily
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        for chunk in image_file.chunks():
            tmp_file.write(chunk)
        tmp_file.close()

        # Call Gemini
        result = analyze_civic_issue(tmp_file.name, user_text)

        return JsonResponse(result, safe=False)

    return JsonResponse({"error": "Only POST allowed"}, status=405)
