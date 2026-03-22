"""
voice.py - Pillar 1: Input Layer

Handles two input paths:
    1. Voice: Arabic audio -> Whisper ASR -> text
    2. Text: Direct text input

Both paths produce the same output:
    validated text + 768-dim embedding + sentiment label

All models are lazy-loaded to avoid consuming 4GB+ RAM at startup.
Whisper only loads if voice input is actually used.

ANTI-HALLUCINATION: This module only TRANSCRIBES or PASSES THROUGH
human text. It never generates, paraphrases, or modifies content.
The embedding and sentiment are metadata ABOUT the human text.
"""

import numpy as np

import config


class InputProcessor:
    """
    Processes voice or text input into a structured format for deliberation.

    Usage:
        processor = InputProcessor()

        # Text mode:
        result = processor.process_input(text="نحتاج مدارس أفضل")

        # Voice mode:
        result = processor.process_input(audio_path="recording.wav")

        # result = {
        #     "text": "نحتاج مدارس أفضل",
        #     "embedding": np.ndarray of shape (768,),
        #     "sentiment": "positive",
        #     "sentiment_score": 0.85,
        # }
    """

    def __init__(self):
        self._whisper_model = None
        self._embedding_model = None
        self._sentiment_analyzer = None

    # --- Lazy loaders (minimize memory until actually needed) ---

    def _load_whisper(self):
        """Load Whisper ASR model (~1GB for 'base')."""
        import whisper
        self._whisper_model = whisper.load_model(config.WHISPER_MODEL_SIZE)

    def _load_embedding_model(self):
        """Load sentence-transformers model (~400MB)."""
        from sentence_transformers import SentenceTransformer
        self._embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)

    def _load_sentiment(self):
        """Load camel-tools Arabic sentiment analyzer."""
        from camel_tools.sentiment import SentimentAnalyzer
        self._sentiment_analyzer = SentimentAnalyzer.pretrained(config.SENTIMENT_MODEL)

    # --- Core operations ---

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe Arabic audio to text using Whisper.

        Requires ffmpeg installed and on PATH for audio decoding.
        Whisper's 'base' model handles MSA well and Syrian dialect acceptably.
        language="ar" forces Arabic decoding (prevents misidentification as
        Turkish or Persian, which happens with some Syrian dialect audio).

        Args:
            audio_path: Path to audio file (.wav, .mp3, .ogg, etc.)

        Returns:
            Transcribed text string
        """
        if self._whisper_model is None:
            self._load_whisper()
        result = self._whisper_model.transcribe(
            audio_path,
            language=config.WHISPER_LANGUAGE,
        )
        return result["text"].strip()

    def validate_statement(self, text: str) -> str:
        """
        Enforce Polis-style constraints on statement text.

        Rules:
            - Cannot be empty
            - Cannot exceed 140 characters (forces concise ideas)
            - Whitespace is trimmed

        The 140-char limit is a deliberate Polis design choice:
        short statements are easier to vote on, harder to hide
        manipulation in, and equalize participation between
        eloquent speakers and everyone else.
        """
        text = text.strip()
        if not text:
            raise ValueError("Statement cannot be empty")
        if len(text) > config.MAX_STATEMENT_LENGTH:
            raise ValueError(
                f"Statement exceeds {config.MAX_STATEMENT_LENGTH} characters "
                f"(got {len(text)}). Please shorten your statement."
            )
        return text

    def compute_embedding(self, text: str) -> np.ndarray:
        """
        Compute a 768-dimensional semantic embedding for the text.

        Uses paraphrase-multilingual-mpnet-base-v2 which supports Arabic
        natively. The embedding captures the MEANING of the text, not
        just the words. Two statements saying the same thing in different
        ways will have similar embeddings.

        This is used for:
            - Semantic similarity between statements (future: deduplication)
            - Stored as metadata, NOT used in the vote-based clustering

        Returns:
            np.ndarray of shape (768,) with float32 values
        """
        if self._embedding_model is None:
            self._load_embedding_model()
        return self._embedding_model.encode(text)

    def analyze_sentiment(self, text: str) -> tuple:
        """
        Classify Arabic text sentiment.

        Returns (label, confidence_score) where:
            label: "positive", "negative", or "neutral"
            confidence_score: float 0.0-1.0

        Uses camel-tools with the CAMeL-Lab arabert model, trained on
        Arabic social media and news text. Works best on MSA; Syrian
        dialect accuracy is lower but acceptable for prototype.

        The sentiment is used in Pillar 3 for the Fear Heatmap:
        negative-sentiment statements tagged with geographic locations
        reveal where communities share security or economic concerns.
        """
        if self._sentiment_analyzer is None:
            self._load_sentiment()
        label = self._sentiment_analyzer.predict_sentence(text)
        # camel-tools returns string label; confidence extraction would
        # require accessing model logits directly. For prototype, we
        # return 0.0 and rely on the label alone.
        return label, 0.0

    def process_input(self, audio_path: str = None, text: str = None) -> dict:
        """
        Full input pipeline: input -> transcription -> validation -> embedding -> sentiment.

        This is the main entry point. Accepts either voice or text input,
        processes it through the full pipeline, and returns a structured dict
        ready to be stored via models.add_statement().

        The pipeline is strictly one-directional:
            human input -> machine analysis -> structured output
        At no point does any AI model generate or modify the human's words.

        Args:
            audio_path: Path to audio file (used when INPUT_MODE == "voice")
            text: Direct text input (used when INPUT_MODE == "text")

        Returns:
            dict with keys: text, embedding, sentiment, sentiment_score
        """
        # Determine input source
        if audio_path and text:
            raise ValueError("Provide either audio_path or text, not both")
        if audio_path:
            raw_text = self.transcribe_audio(audio_path)
        elif text:
            raw_text = text
        else:
            raise ValueError("Must provide either audio_path or text")

        # Validate (140-char limit, non-empty)
        validated = self.validate_statement(raw_text)

        # Compute embedding (768-dim semantic vector)
        embedding = self.compute_embedding(validated)

        # Classify sentiment (positive/negative/neutral)
        sentiment, score = self.analyze_sentiment(validated)

        return {
            "text": validated,
            "embedding": embedding,
            "sentiment": sentiment,
            "sentiment_score": score,
        }
