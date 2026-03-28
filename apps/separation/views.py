from pathlib import Path

from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SeparationJob
from .serializers import CreateJobSerializer, MixRequestSerializer, SeparationJobSerializer
from .services import export_mix, get_output_root, run_demucs


class HealthView(APIView):
    def get(self, request):
        return Response({"ok": True})


# class CreateJobView(APIView):
#     def post(self, request):
#         serializer = CreateJobSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         upload = serializer.validated_data["file"]
#         job = SeparationJob.objects.create(source_file=upload, status=SeparationJob.Status.PROCESSING)

#         try:
#             source_path = Path(job.source_file.path)
#             output_dir = get_output_root() / str(job.id)
#             result_dir = run_demucs(source_path, output_dir)
#             job.status = SeparationJob.Status.COMPLETED
#             job.metadata = {"output_dir": str(result_dir)}
#             job.save(update_fields=["status", "metadata", "updated_at"])
#         except Exception as exc:  # pragma: no cover
#             job.status = SeparationJob.Status.FAILED
#             job.error_message = str(exc)
#             job.save(update_fields=["status", "error_message", "updated_at"])

#         return Response(SeparationJobSerializer(job).data, status=status.HTTP_201_CREATED)

class CreateJobView(APIView):
    def post(self, request):
        serializer = CreateJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload = serializer.validated_data["file"]
        job = SeparationJob.objects.create(
            source_file=upload,
            status=SeparationJob.Status.PROCESSING
        )

        # 🚀 DEMO MODE (skip demucs)
        job.status = SeparationJob.Status.COMPLETED
        job.metadata = {
                "files": {
        "vocals": f"{base_url}/media/outputs/4bc926d7-0bb1-4329-8fd3-09cb7d1f0aba/htdemucs/Nee_Singam_Dhan_Song_Download_Pagalworld_Mp3_koDaLZB/vocals.mp3",
        "drums": f"{base_url}/media/outputs/4bc926d7-0bb1-4329-8fd3-09cb7d1f0aba/htdemucs/Nee_Singam_Dhan_Song_Download_Pagalworld_Mp3_koDaLZB/drums.mp3",
        "bass": f"{base_url}/media/outputs/4bc926d7-0bb1-4329-8fd3-09cb7d1f0aba/htdemucs/Nee_Singam_Dhan_Song_Download_Pagalworld_Mp3_koDaLZB/bass.mp3",
        "other": f"{base_url}/media/outputs/4bc926d7-0bb1-4329-8fd3-09cb7d1f0aba/htdemucs/Nee_Singam_Dhan_Song_Download_Pagalworld_Mp3_koDaLZB/other.mp3"
    }
            
            # "output_dir": "demo/path"
        
        }
        job.save(update_fields=["status", "metadata", "updated_at"])

        return Response({
            "id": str(job.id),
            "status": "completed",
            "message": "Demo mode - processing skipped"
        }, status=status.HTTP_201_CREATED)

class JobDetailView(APIView):
    def get(self, request, job_id):
        job = SeparationJob.objects.filter(id=job_id).first()
        if not job:
            raise Http404("Job not found")
        return Response(SeparationJobSerializer(job).data)


class DownloadStemView(APIView):
    def get(self, request, job_id, stem):
        job = SeparationJob.objects.filter(id=job_id).first()
        if not job or job.status != SeparationJob.Status.COMPLETED:
            raise Http404("Job not completed")
        output_dir = Path(job.metadata.get("output_dir", ""))
        if not output_dir.exists():
            raise Http404("Output not found")

        filename = "no_vocals" if stem in {"instrumental", "music"} else stem
        for ext in [".mp3", ".wav", ".flac"]:
            candidate = output_dir / f"{filename}{ext}"
            if candidate.exists():
                return FileResponse(open(candidate, "rb"), as_attachment=True, filename=candidate.name)
        raise Http404("Stem not found")


class MixStemView(APIView):
    def post(self, request, job_id):
        job = SeparationJob.objects.filter(id=job_id).first()
        if not job or job.status != SeparationJob.Status.COMPLETED:
            raise Http404("Job not completed")

        serializer = MixRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        output_dir = Path(job.metadata.get("output_dir", ""))
        if not output_dir.exists():
            raise Http404("Output not found")

        stems = serializer.validated_data["stems"]
        output_name = serializer.validated_data.get("output_name") or "mix"
        mixed_file = export_mix(output_dir, stems, output_name)

        return FileResponse(open(mixed_file, "rb"), as_attachment=True, filename=mixed_file.name)
