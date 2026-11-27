# grok-imagine-video-1.5

Adapted model card. Sales copy was removed. This card does not quote a live price.

- Kind: video
- Provider family: xai
- Label: Grok Imagine Video 1.5
- Input modes: keyframes_to_video, image_to_video, text_to_video
- Mode options: unspecified
- Resolutions: 480p, 720p, 1080p
- Durations (seconds): 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
- Aspect ratios: auto, 9:16, 16:9, 1:1, 2:3, 3:2, 4:3, 3:4
- Inline @ aliases: no
- Prompt language: en
- Prompt semantics: compiled_prompt

## Editorial note

Первый и последний кадры можно задавать отдельно. До четырёх промежуточных кадров строго внутри ролика, с интервалом не менее ⅓ секунды. Петля использует одно изображение для начала и конца. В 480p и 720p можно сочетать кадры с набором до 7 референсов. В 1080p доступна генерация из текста или одного первого кадра. Промпт необязателен при изображении.

## OpenMontage use

Edit-source means mode `edit` and field `sourceVideo`. Motion-reference means the clip controls motion and camera only. Rank this card with `lib.scoring`, then show a launch card before any paid call.
