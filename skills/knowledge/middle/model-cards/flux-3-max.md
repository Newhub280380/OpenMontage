# flux-3-max

Adapted model card. Sales copy was removed. This card does not quote a live price.

- Kind: video
- Provider family: fal
- Label: FLUX 3 Max
- Input modes: text_to_video, image_to_video, first_last_frame_to_video, keyframes_to_video
- Mode options: unspecified
- Resolutions: 720p, 1080p
- Durations (seconds): 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
- Aspect ratios: auto, 21:9, 2:1, 16:9, 4:3, 1:1, 3:4, 9:16
- Inline @ aliases: no
- Prompt language: en
- Prompt semantics: compiled_prompt

## Editorial note

Создаёт видео по тексту, первому кадру, первому и последнему кадрам или 1–10 ключевым кадрам. Позиции ключевых кадров задаются на таймлайне 24 кадра/с. Длительность — целые 5–20 секунд, разрешение — 720p или 1080p. Auto выбирает 16:9 для текста и формат первого изображения для кадров. Звук включён по умолчанию; уровень проработки промпта и seed настраиваются отдельно.

## OpenMontage use

Edit-source means mode `edit` and field `sourceVideo`. Motion-reference means the clip controls motion and camera only. Rank this card with `lib.scoring`, then show a launch card before any paid call.
