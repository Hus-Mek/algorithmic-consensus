"""
main.py - CLI Entry Point for Algorithmic Consensus

Wires together all three pillars via Click CLI commands.

Usage:
    python main.py init                          # Create database
    python main.py seed                          # Load test data
    python main.py add-participant --location X  # Register participant
    python main.py submit ID --text "..."        # Submit statement
    python main.py submit ID --audio file.wav    # Submit via voice
    python main.py statements                    # List all statements
    python main.py vote ID STMT_ID agree         # Cast vote
    python main.py status                        # Show statistics
    python main.py analyze                       # Run full analysis
"""

import os
import sys

# Fix Windows console encoding for Arabic text
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import click

import config
import models


@click.group()
def cli():
    """Algorithmic Consensus - AI-driven deliberative framework for post-conflict peacebuilding."""
    pass


@cli.command()
def init():
    """Initialize the database. Run this first."""
    conn = models.init_db()
    conn.close()
    click.echo(f"Database created at {config.DB_PATH}")
    click.echo("Run 'python main.py seed' to load test data, or 'python main.py add-participant' to start fresh.")


@cli.command()
def seed():
    """Populate database with synthetic test data (15 participants, 10 statements, votes)."""
    conn = models.init_db()
    models.seed_data(conn)
    conn.close()
    click.echo("Seed data loaded. Run 'python main.py status' to see stats.")


@cli.command("add-participant")
@click.option("--location", default="", help="Coarse geographic location (city name, e.g. 'Damascus')")
def add_participant(location):
    """Register a new anonymous participant."""
    conn = models.init_db()
    p = models.create_participant(conn, location=location)
    conn.close()
    click.echo(f"Created: {p.id}")
    if location:
        click.echo(f"Location: {location}")
    click.echo("Use this ID to submit statements and vote.")


@cli.command()
@click.argument("participant_id")
@click.option("--text", default=None, help="Statement text (max 140 characters)")
@click.option("--audio", default=None, help="Path to audio file for voice input (.wav, .mp3, .ogg)")
def submit(participant_id, text, audio):
    """Submit a statement to the deliberation.

    PARTICIPANT_ID is the anonymous ID from add-participant.
    Provide either --text or --audio (not both).
    """
    if not text and not audio:
        click.echo("Error: Provide either --text or --audio", err=True)
        sys.exit(1)
    if text and audio:
        click.echo("Error: Provide either --text or --audio, not both", err=True)
        sys.exit(1)

    from voice import InputProcessor
    processor = InputProcessor()

    try:
        if audio:
            click.echo("Transcribing audio...")
            result = processor.process_input(audio_path=audio)
            click.echo(f"Transcribed: \"{result['text']}\"")
        else:
            result = processor.process_input(text=text)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    conn = models.init_db()
    stmt = models.add_statement(
        conn,
        author_id=participant_id,
        text=result["text"],
        embedding=result["embedding"],
        sentiment=result["sentiment"],
        sentiment_score=result["sentiment_score"],
    )
    conn.close()

    click.echo(f"Statement #{stmt.id} submitted")
    click.echo(f"Sentiment: {result['sentiment']}")


@cli.command()
def statements():
    """List all statements available for voting (no author info shown - privacy)."""
    conn = models.init_db()
    stmts = models.get_all_statements(conn)
    conn.close()

    if not stmts:
        click.echo("No statements yet. Use 'python main.py submit' to add one.")
        return

    click.echo(f"\n{'ID':<6} {'Statement':<60} {'Sentiment':<12}")
    click.echo("-" * 78)
    for s in stmts:
        # Truncate for display if needed
        display_text = s.text if len(s.text) <= 58 else s.text[:55] + "..."
        click.echo(f"{s.id:<6} {display_text:<60} {s.sentiment:<12}")
    click.echo(f"\nTotal: {len(stmts)} statements")


@cli.command()
@click.argument("participant_id")
@click.argument("statement_id", type=int)
@click.argument("value", type=click.Choice(["agree", "disagree", "pass"]))
def vote(participant_id, statement_id, value):
    """Cast a vote on a statement.

    PARTICIPANT_ID: your anonymous ID
    STATEMENT_ID: the statement number to vote on
    VALUE: agree, disagree, or pass
    """
    vote_map = {"agree": 1, "disagree": -1, "pass": 0}
    int_value = vote_map[value]

    conn = models.init_db()
    try:
        v = models.cast_vote(conn, participant_id, statement_id, int_value)
        click.echo(f"Vote recorded: {value} on statement #{statement_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        conn.close()


@cli.command()
def status():
    """Show current deliberation statistics."""
    conn = models.init_db()
    stats = models.get_stats(conn)
    conn.close()

    click.echo("\n=== Deliberation Status ===")
    click.echo(f"Participants:  {stats['participants']}")
    click.echo(f"Statements:    {stats['statements']}")
    click.echo(f"Votes cast:    {stats['votes']}")
    click.echo(f"Vote coverage: {stats['vote_coverage_pct']}%")

    if stats['participants'] < config.MIN_PARTICIPANTS_FOR_ANALYSIS:
        click.echo(
            f"\nNote: Need at least {config.MIN_PARTICIPANTS_FOR_ANALYSIS} "
            f"participants for reliable analysis "
            f"(currently {stats['participants']})."
        )
    if stats['vote_coverage_pct'] < 30 and stats['votes'] > 0:
        click.echo("\nWarning: Vote coverage below 30%. Encourage participants to vote on more statements.")


@cli.command()
def analyze():
    """Run the full deliberation analysis pipeline.

    Steps:
    1. Build vote matrix from all votes
    2. PCA dimensionality reduction to 2D
    3. K-means clustering to find opinion groups
    4. Bridge statement detection (ideas with cross-group agreement)
    5. Compute Unity Score and Consensus Index
    6. Generate fear heatmap and cluster visualization
    7. Save report (JSON + Markdown)
    """
    from deliberation import DeliberationEngine
    from consensus import ConsensusAnalyzer

    conn = models.init_db()

    click.echo("\n=== Running Deliberation Analysis ===\n")

    # Step 1-4: Deliberation engine
    engine = DeliberationEngine(conn)
    try:
        result = engine.run_full_analysis()
    except ValueError as e:
        click.echo(f"Cannot analyze: {e}", err=True)
        conn.close()
        sys.exit(1)

    meta = result["metadata"]
    click.echo(f"Participants: {meta['n_participants']}")
    click.echo(f"Statements analyzed: {meta['n_statements']}")
    click.echo(f"Vote coverage: {meta['vote_coverage_pct']}%")
    click.echo(f"PCA explained variance: {meta['pca_explained_variance']}")
    click.echo(f"Clusters found: {meta['cluster_count']} (silhouette: {meta['silhouette_score']})")
    click.echo("")

    # Print cluster sizes
    for c in result["clusters"]:
        click.echo(f"  {c.label}: {len(c.member_ids)} participants")
    click.echo("")

    # Step 5-7: Consensus analysis and reporting
    analyzer = ConsensusAnalyzer(conn, result)
    report = analyzer.generate_report()

    unity = report["metrics"]["unity_score"]
    ci = report["metrics"]["consensus_index"]

    click.echo(f"Unity Score: {unity}")
    click.echo(f"Consensus Index: {ci}")
    click.echo("")

    # Print bridge statements
    bridges = report["bridge_statements"]
    if bridges:
        click.echo(f"Bridge Statements Found: {len(bridges)}")
        click.echo("-" * 50)
        for i, b in enumerate(bridges, 1):
            click.echo(f"  {i}. \"{b['text']}\"")
            click.echo(f"     Score: {b['bridge_score']} | Agreed by {b['clusters_agreeing']} groups")
    else:
        click.echo("No bridge statements found. The groups have not found common ground yet.")

    click.echo("")
    click.echo(f"Reports saved to: {config.OUTPUT_DIR}")
    for key, path in report.get("output_paths", {}).items():
        click.echo(f"  {key}: {path}")

    conn.close()


if __name__ == "__main__":
    cli()
