# AI Chat Task

Полноценное full-stack приложение для диалога с LLM через OpenRouter. Проект состоит из трех частей:

- `frontend/` — пользовательский интерфейс на Next.js;
- `backend/` — API, бизнес-логика и работа с контекстом на FastAPI;
- `docker-compose.yml` + `Makefile` — инфраструктура локального запуска и ежедневного управления сервисами.

Этот README описывает не только запуск, но и объясняет, почему система устроена именно так.

## Что решает этот проект

Приложение должно было закрыть несколько задач одновременно:

- вести историю чатов без обязательной регистрации пользователя;
- отдавать ответ модели потоково, а не ждать целиком готовый текст;
- не терять качество ответа на длинных диалогах;
- оставаться простым в локальной разработке и понятным при проверке кода.

Отсюда и выросла текущая архитектура.

## Почему выбрана именно такая архитектура

### Монорепозиторий

Backend, frontend и инфраструктура лежат в одном репозитории, потому что проект тесно связан по контрактам:

- frontend зависит от shape API и streaming-формата;
- backend зависит от конкретного сценария UI и таймингов стрима;
- инфраструктура должна запускать обе части одним набором команд.

Для такой задачи монорепозиторий проще, чем разнос по разным репозиториям с отдельной синхронизацией версий.

### Разделение на frontend и backend

Хотя проект относительно компактный, backend и frontend разделены физически, потому что у них разный жизненный цикл:

- backend отвечает за данные, LLM orchestration и устойчивость;
- frontend отвечает за UX, optimistic updates и потоковое отображение;
- это разные типы сложности и разные точки отказа.

Такое разделение дает более чистую модель, чем попытка собрать все в один Next.js-only проект.

### BFF + API

Во frontend используется route handler `app/api/v1/[...path]/route.ts`, который работает как BFF-переходник к backend.

Это решение выбрано потому что:

- браузер работает с same-origin API;
- backend origin можно менять через env, не трогая клиентский код;
- проще проксировать `X-Client-Id` и системные заголовки;
- уменьшается количество CORS-проблем и сетевой связанности.

### Потоковый ответ через SSE

Ответ модели передается через SSE, а не через WebSocket.

Причина простая: трафик здесь односторонний. Клиент отправляет один HTTP-запрос и получает поток токенов назад. Для этого SSE проще:

- меньше инфраструктурной сложности;
- стандартный HTTP lifecycle;
- проще логировать и воспроизводить;
- достаточно для UX “печатания ответа”.

### Суммаризация старых сообщений внутри backend

Длинные диалоги обрабатываются не за счет безлимитного контекста, а через controlled summarization:

- старые сообщения агрегируются в summary;
- последние сообщения остаются в живом контексте;
- backend сам решает, когда запускать суммаризацию и сколько сообщений сворачивать.

Это дешевле и проще, чем вводить vector store или отдельный memory-service для проекта такого масштаба.

## Почему выбран именно этот стек

### Frontend

- `Next.js 16` — routing, BFF route handlers, единая среда для dev и deploy.
- `React 19` — зрелая модель UI и экосистема под потоковые интерфейсы.
- `TanStack Query` — серверный state, кеш чатов и сообщений, optimistic updates.
- `Zustand` — компактный store для ephemeral streaming-state.
- `Tailwind CSS` — быстрый UI-слой без тяжелой собственной design-system инфраструктуры.

Причина выбора: frontend здесь должен быть быстрым в разработке, предсказуемым в навигации и хорошо переносить частые обновления состояния во время стрима.

### Backend

- `FastAPI` — асинхронный HTTP-слой, удобная DI-модель, OpenAPI из коробки.
- `SQLAlchemy Async` — работа с PostgreSQL без разрыва с async-пайплайном.
- `Alembic` — контроль схемы и воспроизводимые миграции.
- `PostgreSQL` — надежное хранение чатов и сообщений с транзакциями и индексами.
- `OpenRouter` — единая точка доступа к моделям без привязки к одному провайдеру.

Причина выбора: backend должен устойчиво обслуживать стриминг, хранить историю и содержать прозрачную бизнес-логику без лишней платформенной сложности.

### Infrastructure

- `Docker Compose` — локальный orchestration для `postgres`, `backend`, `frontend`.
- раздельные env-файлы — `backend/.env` для backend/postgres и `frontend/.env` для frontend/BFF.
- `Makefile` — короткие операционные команды без необходимости помнить длинные compose-вызовы.

Причина выбора: у проекта должен быть низкий порог запуска и повторяемый dev workflow.

## Структура репозитория

```text
ai_chat_task/
├── backend/              # FastAPI API, domain logic, DB, migrations
├── frontend/             # Next.js UI, BFF proxy, streaming client
├── docker-compose.yml    # Local infrastructure
├── Makefile              # Day-to-day project commands
└── README.md             # System overview and architecture rationale
```

## Документация по частям системы

- [backend/README.md](backend/README.md) — зачем backend устроен через `api / services / repositories`, почему FastAPI, PostgreSQL, Alembic и SSE.
- [frontend/README.md](frontend/README.md) — зачем нужен BFF, почему state разделен между TanStack Query и Zustand, почему структура `shared / entities / features / widgets`.

## Поток запроса: от ввода до сохранения ответа

Ниже — основной runtime flow:

1. Пользователь вводит сообщение во frontend.
2. Если это новый диалог, создается чат и frontend переходит на `/chat/{id}`.
3. Frontend кладет user message и пустой assistant message в cache optimistically.
4. Frontend отправляет POST на backend и начинает читать SSE stream.
5. Backend записывает user message в PostgreSQL.
6. Backend собирает контекст: system prompt + summary + актуальные сообщения.
7. Backend вызывает LLM и отдает chunk-ответы клиенту по мере генерации.
8. После завершения потока backend сохраняет итоговый assistant message.
9. Затем backend отдельно запускает post-stream задачи:
   title generation для первого сообщения;
   summarization, если диалог стал слишком длинным.

Такой пайплайн выбран потому что он балансирует UX и надежность:

- пользователь быстро видит начало ответа;
- база остается источником истины;
- постобработка не тормозит streaming.

## Почему приняты именно такие ключевые решения

### Анонимный `X-Client-Id`, а не полноценная auth-система

На текущем этапе задача — чат, а не identity-platform. Поэтому выбран анонимный UUID в заголовке:

- это достаточно для изоляции данных по пользователю;
- не надо тянуть регистрацию, JWT, refresh flow и UI вокруг этого;
- проект остается сфокусированным на LLM-сценарии.
- проект все еще можно масштабировать и подключить полноценную авторизацию без сильных изменений в коде или архитектуре БД

Минус очевиден: это не production-grade auth. Но для текущей постановки это правильный компромисс.

### Title generation после первого сообщения

Название чата генерируется асинхронно и только после первого сообщения, потому что:

- до первого сообщения у чата нет смысла;
- не нужно просить пользователя называть чат руками;
- генерация названия не влияет на first-token latency.


## Быстрый старт

### Через Docker

```bash
make env-init
make docker-up-build
```

После запуска:

- frontend: `http://localhost:3000`
- backend docs: `http://localhost:8000/docs`
- backend health: `http://localhost:8000/health`

Что настроить:

- в `backend/.env` задать как минимум `OPENROUTER_API_KEY`;
- `frontend/.env` оставить единым frontend env-файлом; для локального запуска в нем используется `BACKEND_URL=http://localhost:8000`, а в Docker Compose это значение переопределяется на `http://backend:8000`.

### Локально

Backend:

```bash
make env-init
# В backend/.env для локального запуска укажи POSTGRES_HOST=localhost
make backend-install
make backend-migrate
make backend-dev
```

Frontend:

```bash
make frontend-env-init
make frontend-install
make frontend-dev
```

## Makefile

В репозитории есть корневой `Makefile`, чтобы не держать в голове длинные команды.

Основные цели:

- `make help` — показать все доступные команды;
- `make env-init` — подготовить `backend/.env` и `frontend/.env`;
- `make backend-env-init` — подготовить `backend/.env`;
- `make frontend-env-init` — подготовить `frontend/.env`;
- `make docker-up-build` — собрать и поднять весь стек;
- `make docker-down` — остановить стек;
- `make docker-logs-backend` — смотреть логи backend;
- `make docker-db-cli` — зайти в `psql` внутри контейнера;
- `make docker-migrate` — применить миграции внутри backend-контейнера;
- `make backend-dev` — запустить FastAPI локально;
- `make frontend-dev` — запустить Next.js локально;
- `make backend-test` — прогнать backend unit tests;
- `make frontend-lint` — прогнать lint фронтенда.

## Конфигурация окружения

Конфигурация теперь разделена по сервисам.

`backend/.env` используется backend и контейнером PostgreSQL.

Ключевые переменные:

- `OPENROUTER_API_KEY` — ключ доступа к LLM.
- `POSTGRES_HOST` — `postgres` для Docker, `localhost` для локального backend.
- `POSTGRES_PORT` — порт PostgreSQL.
- `POSTGRES_DB` — имя базы.
- `POSTGRES_USER` — пользователь БД.
- `POSTGRES_PASSWORD` — пароль БД.
- `MODEL_NAME` — выбранная модель OpenRouter.
- `MESSAGE_THRESHOLD` — порог для запуска суммаризации.
- `RECENT_MESSAGES_KEPT` — сколько последних сообщений всегда оставлять живыми.
- `SUMMARY_BATCH_SIZE` — размер одного summarization batch.

`frontend/.env` — единый frontend env-файл для локального запуска и Docker Compose.

Ключевая переменная:

- `BACKEND_URL` — upstream для BFF proxy.
- Значение в `frontend/.env`: `http://localhost:8000`
- В Docker Compose это значение переопределяется на `http://backend:8000`, потому что frontend внутри контейнера ходит к backend по имени сервиса.

## Что в проекте сделано сознательно просто

Некоторые вещи не усложнялись специально:

- нет Redis и отдельной очереди;
- нет WebSocket-сервера;
- нет полноценной auth-системы;
- нет vector database;
- нет отдельной design system библиотеки.

Это не упущения, а осознанные ограничения масштаба. Проект решает конкретную задачу и избегает преждевременной платформенной сложности.

## Куда проект можно развивать дальше

- полноценная аутентификация и multi-device сессии;
- асинхронная очередь для post-stream задач;
- observability: tracing, metrics, structured logging;
- более явная политика retries и circuit breaking для LLM;
- покрытие e2e-тестами frontend streaming-сценариев;
- разделение runtime env для local/dev/stage/prod.

Проект выполнен с использованием Claude Code  и  Codex CLI
