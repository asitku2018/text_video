import os
import uuid
import subprocess
from celery import Celery
from gtts import gTTS
from core.config import settings

celery_app = Celery("video_tasks", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@celery_app.task(bind=True)
def process_video_task(self, image_filename: str, text: str, language: str):
    task_id = self.request.id
    base_path = settings.UPLOAD_DIR
    
    image_path = os.path.join(base_path, image_filename)
    audio_path = os.path.join(base_path, f"{task_id}.mp3")
    output_video_path = os.path.join(base_path, f"{task_id}.mp4")

    try:
        self.update_state(state='PROCESSING', meta={'step': 'Generating Audio'})
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(audio_path)

        self.update_state(state='PROCESSING', meta={'step': 'Rendering Video'})
        # FFmpeg command optimized for static image + audio, preventing buffer overflows
        command = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest", # End video when the shortest input (audio) ends
            output_video_path
        ]
        
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Cleanup intermediate files to save disk space
        os.remove(image_path)
        os.remove(audio_path)

        return {"status": "COMPLETED", "video_url": f"/api/v1/videos/download/{task_id}.mp4"}

    except Exception as e:
        self.update_state(state='FAILED', meta={'error': str(e)})
        raise e
