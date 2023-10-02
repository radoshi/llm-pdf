# llm-pdf

# Snippets

# def load_templates(path: Path) -> Optional[TemplateLibrary]:

# path = path / "prompts"

# if path.exists():

# return TemplateLibrary.from_file_or_directory(path)

# else:

# return None

# def init_db(config_dir: Path):

# config_dir.mkdir(parents=True, exist_ok=True)

# db_path = config_dir / "db.sqlite"

# \_ = db.Database.get(db_path)

# def get_cached_response(settings: Settings, messages: list[dict]) -> Optional[Message]:

# record = db.get_last_inserted_row()

# if not record:

# return None

# if (

# record.model != settings.model

# or record.temperature != settings.temperature

# or record.max_tokens != settings.max_tokens

# or record.system_message != messages[0]["content"]

# or record.user_message != messages[1]["content"]

# ):

# return None

# return Message(

# role="assistant",

# content=record.assistant_message,

# )

# def get_code(inputs) -> str:

# files = [f for input in inputs for f in Path.cwd().glob(input)]

# file_name = [f.name for f in files]

# file_texts = [f.read_text() for f in files]

# file_blobs = [

# f"FILENAME: {name}\n`{text}\n`"

# for (name, text) in zip(file_name, file_texts)

# ]

# return "\n---\n".join(file_blobs)

# def get_max_tokens(message: str) -> int:

# return len(message.split(" "))

console = Console()

    # settings = Settings()
    # if not settings.openai_api_key:
    #     openai_api_key = click.prompt("Please enter your OpenAI API key", type=str)
    #     settings.openai_api_key = openai_api_key
    #     # Append OPENAI_API_KEY to settings file
    #     with SETTINGS_FILE.open("a") as f:
    #         f.write(f"OPENAI_API_KEY={openai_api_key}\n")

    # if gpt_4:
    #     settings.model = "gpt-4"

    # vector_client = db.init_vectordb(VECTOR_DB)
    # sqlite_conn = db.init_sqlite(SQLITE_DB)
    # cursor = sqlite_conn.cursor()

    # Lazily index the file
    # db.index(pdfs, vector_client, cursor, EMBED_DIR)

    # init_db(settings.config_dir)

    # if not instructions:
    #     raise click.UsageError("Please provide some instructions.")

    # library = load_templates(settings.config_dir) or load_templates(
    #     Path(__file__).parent.parent
    # )
    # if not library:
    #     raise click.UsageError("No templates found.")

    # if inputs:
    #     code = get_code(inputs)
    #     message = library["coding/input"].message(
    #         code=code, instructions=" ".join(instructions)
    #     )
    # else:
    #     message = library["coding/simple"].message(instructions=" ".join(instructions))

    # messages = [library["coding/system"].message(), message]

    # cached_response = get_cached_response(settings, messages)
    # if no_cache or not cached_response:
    #     with console.status("[bold green]Asking OpenAI..."):
    #         response = openai.ChatCompletion.create(
    #             api_key=settings.openai_api_key,
    #             model=settings.model,
    #             temperature=settings.temperature,
    #             max_tokens=settings.max_tokens,
    #             messages=messages,
    #         )

    #     message = Message.from_message(response.choices[0]["message"])  # type: ignore

    #     db.write(
    #         model=settings.model,
    #         temperature=settings.temperature,
    #         max_tokens=settings.max_tokens,
    #         system_message=messages[0]["content"],
    #         user_message=messages[1]["content"],
    #         assistant_message=message.content,
    #         input_tokens=response.usage["prompt_tokens"],  # type: ignore
    #         output_tokens=response.usage["completion_tokens"],  # type: ignore
    #     )
    # else:
    #     message = cached_response

    # code_block = message.code()
    # if code_block:
    #     console.print(Syntax(code_block.code, code_block.lang, word_wrap=True))
    #     if clipboard:
    #         pyperclip.copy(code_block.code)
    # else:
    #     console.print(f"No code found in message: \n\n{message.content}")
    #     sys.exit(1)

    def _check_collection_exists(self, filenames: list[str]) -> bool:
        file_hash = self._get_file_hash(filenames)
        cursor = self.sqlite.cursor()
        cursor.execute("SELECT id FROM collections WHERE file_hash=?", (file_hash,))
        return cursor.fetchone() is not None

    def _create_tables(self) -> None:
        """Create the tables if they don't exist."""
        cursor = self.sqlite.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                filenames TEXT,
                file_hash TEXT UNIQUE
            )
            """
        )
        self.sqlite.commit()

    def _get_file_hash(self, filenames: list[str]) -> str:
        # Concatenate filenames and hash the result
        concat_filenames = "".join(sorted(filenames))
        return hashlib.sha256(concat_filenames.encode()).hexdigest()
