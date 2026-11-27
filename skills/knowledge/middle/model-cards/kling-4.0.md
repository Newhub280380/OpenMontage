# kling-4.0

Adapted model card. Sales copy was removed. This card does not quote a live price.

- Kind: video
- Provider family: kie
- Label: Kling 4.0
- Input modes: text_to_video, image_to_video, video_reference
- Mode options: unspecified
- Resolutions: 720p, 1080p
- Durations (seconds): 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30
- Aspect ratios: auto, 16:9, 9:16, 1:1, 21:9, adaptive
- Inline @ aliases: no
- Prompt language: en
- Prompt semantics: compiled_prompt

## Editorial note

Создаёт видео по тексту, первому и последнему кадрам с промежуточными изображениями в заданном порядке или референсам. Промежуточные кадры не задают точное время. Всего до min(длительность + 1, 10) кадров. Референсы: до 10 изображений, 5 видео по 2–30 секунд и 3 голосов, не более 15 материалов. В промпте используйте @image_1, @video_1, @voice_1; для кадров — @first_frame, @keyframe_1, @last_frame. С видео-референсами стоимость учитывает полную длительность всех входных видео и результата, минимум две длительности результата.

## OpenMontage use

Edit-source means mode `edit` and field `sourceVideo`. Motion-reference means the clip controls motion and camera only. Rank this card with `lib.scoring`, then show a launch card before any paid call.
