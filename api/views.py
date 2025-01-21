from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.http import FileResponse
from PIL import Image
from pytubefix import YouTube
import threading
import os


class ConvertImageView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        file = request.FILES.get("file")
        target_format = request.data.get("target_format")

        if not file or not target_format:
            return Response({"error": "Arquivo ou formato ausente."}, status=400)

        # SALVANDO TEMPORARIAMENTE
        temp_dir = "temp_images"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f"temp_{file.name}")

        with open(temp_file_path, "wb") as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)

        try:
            # AQUI CONVERTE O ARQUIVO
            with Image.open(temp_file_path) as img:
                if img.mode == "RGBA":
                    img = img.convert("RGB")

                valid_formats = ["jpeg", "png", "gif"]
                if target_format.lower() not in valid_formats:
                    return Response({"error": "Formato inválido."}, status=400)

                original_name = os.path.splitext(file.name)[0]  # Nome sem extensão
                new_filename = f"{original_name}.{target_format.lower()}"
                converted_file_path = f"{temp_dir}/{new_filename}"
                img.save(converted_file_path, target_format.upper())

            # AQUI RETORNA O ARQUIVO
            response = FileResponse(
                open(converted_file_path, "rb"),
                as_attachment=True,
                filename=os.path.basename(converted_file_path),
                content_type=f"image/{target_format.lower()}",
            )

            threading.Thread(
                target=self.cleanup_files,
                args=(temp_file_path, converted_file_path),
                daemon=True,
            ).start()
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        return response

    def cleanup_files(self, *file_paths):
        import time
        time.sleep(5)  # Espera 5 segundos para garantir que o arquivo não esteja em uso
        for path in file_paths:
            if os.path.exists(path):
                os.remove(path)


class DownloadVideoView(APIView):
    def post(self, request, format=None):
        url = request.data.get("url")

        if not url:
            return Response({"error": "URL ausente."}, status=400)

        try:
            yt = YouTube(url)
            stream = yt.streams.get_highest_resolution()

            file_path = stream.download(output_path="downloads/")
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        # Retornar o arquivo baixado como resposta
        with open(file_path, "rb") as video_file:
            response = Response(video_file.read(), content_type="video/mp4")
            response["Content-Disposition"] = f"attachment; filename='{yt.title}.mp4'"
            return response
        
