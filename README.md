# SimpleOCR

Десктопное приложение для Windows, которое копирует текст с любой
картинки или области экрана с помощью **PaddleOCR**. Поддержка русского
и английского (и других языков) одновременно, угловой классификатор для
повёрнутого текста.

## Возможности

- **Захват области экрана** — глобальная горячая клавиша `Ctrl+Shift+S`,
  экран затемняется, выделяете прямоугольник мышью (как в «Ножницах»).
- **OCR из файла** — `.png .jpg .jpeg .bmp .webp .tiff`.
- **OCR из буфера обмена** — распознаёт картинку из буфера.
- **PaddleOCR** с `use_angle_cls=True`, языки переключаются в настройках.
- **Редактируемое поле результата** + автокопирование в буфер +
  кнопка «Скопировать снова». Переносы строк восстанавливаются по
  структуре изображения (сверху вниз, слева направо).
- **История** — последние 10 распознаваний, клик восстанавливает текст.
- **Системный трей** — фоновая работа, горячая клавиша работает всегда.
- **Индикатор первого запуска** — окно прогресса при разовой загрузке
  моделей.

Настройки, история и кеш моделей хранятся в `%APPDATA%\SimpleOCR\`
(модели — в `%APPDATA%\SimpleOCR\models\`, а не в `C:\Users\<user>\.paddleocr`).

## Системные требования

- **Windows 10 или новее** (64-bit).
- **Visual C++ Redistributable 2019 или новее** — обязательно для
  PaddlePaddle. Скачать: aka.ms/vs/17/release/vc_redist.x64.exe
- **Минимум 4 ГБ ОЗУ**.
- **Интернет при первом запуске** — для загрузки моделей
  (~10–50 МБ на язык). Дальше работает офлайн.
- Python **3.10 или 3.11** для запуска из исходников / сборки
  (PaddlePaddle стабильнее на 3.10–3.11, **избегайте 3.12+**).

## Запуск из исходников

```cmd
git clone <repo>
cd scantext
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r ocr_app\requirements.txt
python ocr_app\resources\make_icon.py   :: создать icon.ico (нужен Pillow)
python -m ocr_app.main
```

Первый запуск: появится окно «Загрузка моделей распознавания, это
разовая операция» — дождитесь окончания (5–15 сек + загрузка).

## Сборка .exe (только на Windows)

> `.exe` нельзя собрать на Linux/macOS — PyInstaller создаёт
> платформозависимый бинарник, и PaddlePaddle нужен Windows-рантайм.
> Сборку выполняйте на Windows-машине.

```cmd
.venv\Scripts\activate
pip install -r ocr_app\requirements.txt
python ocr_app\resources\make_icon.py
cd ocr_app
pyinstaller build.spec
```

Готовый файл: **`ocr_app\dist\SimpleOCR.exe`** (~200–300 МБ —
PaddlePaddle тянет большие зависимости). Это `--onefile --windowed`
с иконкой `resources\icon.ico`.

### Офлайн-сборка с моделями

Запустите приложение хотя бы раз, чтобы модели скачались в
`%APPDATA%\SimpleOCR\models`. Затем раскомментируйте блок `MODELS`
в `build.spec` и пересоберите — модели попадут внутрь `.exe` и
интернет при первом запуске не понадобится.

### Возможные проблемы сборки

- *ModuleNotFoundError для paddle/skimage/scipy в собранном exe* —
  добавьте недостающий модуль в `hiddenimports` в `build.spec`.
- *Антивирус удаляет exe* — ложное срабатывание PyInstaller onefile;
  добавьте в исключения или собирайте `--onedir`.
- *Долгий первый старт onefile* — нормально: распаковка во временную
  папку. Для скорости используйте `--onedir`.

## Структура проекта

```
ocr_app/
├── main.py
├── ui/
│   ├── main_window.py
│   ├── snip_overlay.py
│   ├── settings_dialog.py
│   └── loading_dialog.py
├── core/
│   ├── config.py        # пути %APPDATA%, настройки
│   ├── ocr_engine.py    # обёртка над PaddleOCR
│   ├── workers.py       # QThread (warmup + OCR)
│   ├── hotkeys.py
│   ├── history.py
│   └── clipboard.py
├── resources/
│   ├── make_icon.py     # генератор icon.ico
│   └── icon.ico         # создаётся make_icon.py
├── tests/
│   └── test_ocr_engine.py
├── requirements.txt
└── build.spec
```

## Тесты

Проверка логики восстановления строк (PaddleOCR не нужен):

```cmd
pip install pytest
python -m pytest ocr_app\tests\ -q
```

## Лицензия

Для личного использования. PaddleOCR/PaddlePaddle — Apache-2.0.
