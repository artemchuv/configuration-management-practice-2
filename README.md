# Практическое задание №2 — вариант 22

Инструмент визуализации графа зависимостей Maven. Программа получает
прямые зависимости из POM-файлов репозитория без Maven и сторонних
библиотек для анализа зависимостей. Граф строится итеративным DFS,
сохраняется как SVG и как текст диаграммы PlantUML.

## Требования

- Python 3.10+;
- интернет для настоящего Maven-репозитория;
- для тестового режима интернет не нужен.

## Структура

```text
src/main.py          CLI и проверка параметров
src/model.py         граф, DFS, обратные связи, ASCII-дерево
src/repository.py    загрузка POM и JSON-фикстуры
src/render.py        генерация PlantUML и SVG
tests/fixtures/     тестовый репозиторий
tests/test_graph.py  автоматические проверки
run.sh / run.bat     запуск в Linux / Windows
```

## Параметры

| Параметр | Значение |
| --- | --- |
| `--package` | `group:artifact:version` или большая латинская буква в тестовом режиме |
| `--repository` | URL Maven-репозитория или путь к JSON-файлу |
| `--test` | читать тестовый JSON-репозиторий |
| `--output` | путь для файла SVG; рядом появится `.puml` |
| `--ascii` | напечатать дерево зависимостей |
| `--max-depth` | максимальная глубина обхода, неотрицательное целое |
| `--exclude` | подстрока для исключения пакетов |
| `--reverse` | обратные зависимости в тестовом режиме |

Параметры проверяются через `argparse`. Неверный URL, файл, JSON,
имя пакета или глубина завершают программу с понятным сообщением.

## Демонстрация без интернета

В Linux откройте терминал в корне проекта:

```bash
bash run.sh --package A --repository tests/fixtures/graph.json \
  --test --ascii --max-depth 4 --output output/a.svg
```

В Windows используйте `run.bat` с теми же параметрами.
В графе `A → B → D → A` есть цикл, а `D` доступен также через `C`.
Строка `[cycle]` в дереве показывает место цикла; обход не зависает.

Команда для Windows (PowerShell):

```powershell
.\run.bat --package A --repository tests/fixtures/graph.json --test --ascii --max-depth 4 --output output/a.svg
```

Ещё два примера визуализации:

```bash
bash run.sh --package B --repository tests/fixtures/graph.json \
  --test --ascii --output output/b.svg
bash run.sh --package C --repository tests/fixtures/graph.json \
  --test --ascii --output output/c.svg
```

Проверенные результаты для трёх разных пакетов тестового репозитория:

| Пакет | Результат | Созданные файлы |
| --- | --- | --- |
| `A` | `A → B → D → A [cycle]`; также `A → C → E` | `output/a.svg`, `output/a.puml` |
| `B` | `B → D → A → B [cycle]`; также путь к `C` | `output/b.svg`, `output/b.puml` |
| `C` | `C → D → A → C [cycle]`; также путь к `E` | `output/c.svg`, `output/c.puml` |

Все три команды завершились успешно; SVG можно открыть в VS Code или браузере.
Готовые изображения сохранены в репозитории: [A](examples/a.svg),
[B](examples/b.svg), [C](examples/c.svg). Рядом находятся соответствующие
файлы PlantUML (`.puml`).

Проверка глубины и фильтра:

```bash
bash run.sh --package A --repository tests/fixtures/graph.json \
  --test --ascii --max-depth 1 --exclude C
```

Обратные зависимости `D` (от него зависят `B` и `C`):

```bash
bash run.sh --package D --repository tests/fixtures/graph.json \
  --test --reverse --ascii --output output/reverse-d.svg
```

## Реальный Maven-репозиторий

```bash
bash run.sh --package junit:junit:4.13.2 \
  --repository https://repo.maven.apache.org/maven2 \
  --max-depth 2 --ascii --output output/junit.svg
```

В Windows используйте:

```powershell
.\run.bat --package junit:junit:4.13.2 --repository https://repo.maven.apache.org/maven2 --max-depth 2 --ascii --output output/junit.svg
```

Проверенный вывод программы: `junit:junit:4.13.2 →
org.hamcrest:hamcrest-core:1.3`. Создаются `output/junit.svg` и
`output/junit.puml`.

Программа запрашивает POM напрямую по Maven-адресу и читает элементы
`dependencies`. Исключаются зависимости с `test`, `provided`, `system`,
`import` и `optional=true`; свойства из текущего POM раскрываются.
Зависимости с версиями, указанными только во внешнем parent/BOM,
не включаются: полноценное разрешение Maven здесь не реализовано.
Это ограничение важно при сравнении со штатным `mvn dependency:tree`:
Maven дополнительно учитывает родительские POM, BOM, профили и правила
разрешения версий. Для сравнения выполните в Maven-проекте
`mvn dependency:tree` и сопоставьте прямые связи.

## Проверка

```bash
python3 -m unittest discover -v
```

SVG открывается обычным браузером. Файл `.puml` можно открыть в
PlantUML для просмотра текстовой диаграммы.

## Этапы разработки

1. CLI и параметры конфигурации.
2. Получение прямых зависимостей из Maven POM.
3. Итеративный DFS с глубиной, фильтром, циклами и тестовым режимом.
4. Обратные зависимости.
5. PlantUML, SVG, ASCII и документация.
