# minimax-h3-max

Adapted model card. Sales copy was removed. This card does not quote a live price.

- Kind: video
- Provider family: fal
- Label: H3 Max
- Input modes: text_to_video, image_to_video, video_reference, video_extend, video_insert, video_edit, video_reframe
- Mode options: create, extend, insert, recast, reframe
- Resolutions: 480p, 768p, 1080p, 2k
- Durations (seconds): 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
- Aspect ratios: 21:9, 16:9, 4:3, 1:1, 3:4, 9:16, auto, 9:21
- Inline @ aliases: no
- Prompt language: en
- Prompt semantics: compiled_prompt

## Editorial note

Выбери режим: create — новый ролик 1–15 секунд в 480P/768P/1080P; можно совместить первый и последний кадры с 9 изображениями и 3 видео-референсами (2–15 с каждый, всего до 15 с). Референсы: до 9 изображений, 3 видео и 3 аудио, всего до 12 материалов. Звуковая дорожка заменяет звук, это не LipSync и она несовместима с мультимодальными референсами. Средний кадр требует первый и последний, время middleFrameTimeSec внутри ролика и 480P/768P; extend — продолжение исходника 1,625–60 секунд; insert — новая сцена 5–13 секунд между startTimeSec и resumeTimeSec. recast — замена людей в исходном видео 5–30 секунд по 1–4 фото, каждый план до 15 секунд, промпт необязателен. Recast оплачивается по длител

## OpenMontage use

Edit-source means mode `edit` and field `sourceVideo`. Motion-reference means the clip controls motion and camera only. Rank this card with `lib.scoring`, then show a launch card before any paid call.
