"""
Database seeder: populates the database with sample users and articles.

Also generates SBERT embeddings for all articles and saves them to FAISS.

Usage:
    # With the backend running locally:
    python -m app.seed.seed_data

    # Or directly:
    python backend/app/seed/seed_data.py

What this creates:
    - 1 admin user  : admin@newsplatform.com / Admin@1234
    - 1 demo user   : user@newsplatform.com  / User@1234
    - 12 sample articles across various domains
    - FAISS index with embeddings for all 12 articles
"""

import sys
import os

# Add backend directory to path so imports work when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))

from app.database.db import SessionLocal, engine
from app.database.models import Base, User, Article
from app.utils.security import hash_password
from app.services.embedding_service import get_embedding_service
from app.services.faiss_service import get_faiss_service
from app.core.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


# ── Sample Articles ───────────────────────────────────────────────────────────

SAMPLE_ARTICLES = [
    {
        "title": "SpaceX Successfully Launches Starship Mega-Rocket",
        "content": (
            "SpaceX completed a successful full test flight of its Starship rocket system, "
            "marking a major milestone in the company's goal to reach Mars. The stainless-steel "
            "rocket reached an altitude of 200 km before splashing down in the Indian Ocean. "
            "CEO Elon Musk called it a historic achievement for commercial space travel. "
            "The rocket is the largest and most powerful ever built, standing 120 metres tall "
            "and producing 16 million pounds of thrust at liftoff."
        ),
        "domain": "technology",
        "source": "Space News",
    },
    {
        "title": "Global Leaders Agree on Climate Action Framework",
        "content": (
            "At the annual climate summit, world leaders signed a landmark agreement to cut "
            "carbon emissions by 50% by 2035. The deal includes binding targets for G20 nations "
            "and a $200 billion green technology fund for developing countries. "
            "Scientists say the agreement, if implemented fully, could limit global warming "
            "to 1.5 degrees Celsius above pre-industrial levels. "
            "Key provisions include phasing out coal power plants and tripling renewable energy capacity."
        ),
        "domain": "politics",
        "source": "Reuters",
    },
    {
        "title": "AI Models Surpass Human Performance on Complex Reasoning Tasks",
        "content": (
            "Researchers at a leading AI lab announced that their latest large language model "
            "achieved superhuman scores on the MMLU and GPQA benchmarks. The model demonstrates "
            "advanced mathematical reasoning and scientific problem-solving capabilities. "
            "In head-to-head tests against PhD-level experts, the AI outperformed humans in "
            "physics, chemistry, and biology reasoning tasks. "
            "The breakthrough raises new questions about the pace of AI development and safety."
        ),
        "domain": "technology",
        "source": "MIT Technology Review",
    },
    {
        "title": "World Cup 2026: Host Cities Finalised Across North America",
        "content": (
            "FIFA announced the 16 host cities across the United States, Canada, and Mexico "
            "for the 2026 FIFA World Cup. New York, Los Angeles, Dallas, and Toronto are among "
            "the headline venues for the expanded 48-team tournament. "
            "This will be the first World Cup jointly hosted by three nations. "
            "Infrastructure investments totalling $14 billion are planned across all host cities. "
            "Ticket sales are expected to break all previous World Cup records."
        ),
        "domain": "sports",
        "source": "BBC Sport",
    },
    {
        "title": "Federal Reserve Signals Rate Cuts as Inflation Cools",
        "content": (
            "The Federal Reserve indicated it may begin cutting interest rates in early 2025 "
            "as inflation fell to 2.3% — near its 2% target. Markets rallied sharply on the "
            "news, with the S&P 500 gaining 1.8% and the Nasdaq rising 2.1%. "
            "Fed Chair Jerome Powell said the central bank would proceed carefully with any "
            "rate reductions to avoid reigniting inflation. "
            "Economists expect two to three quarter-point rate cuts over the next 12 months."
        ),
        "domain": "finance",
        "source": "Bloomberg",
    },
    {
        "title": "New Cancer Immunotherapy Shows 80% Response Rate in Trial",
        "content": (
            "A Phase III clinical trial for a novel CAR-T cell therapy demonstrated an 80% "
            "complete response rate in patients with relapsed B-cell lymphoma. "
            "The treatment, developed by a leading biotechnology firm, could receive FDA "
            "approval by mid-2025. Researchers said the therapy works by reprogramming a "
            "patient's own immune cells to identify and destroy cancer cells. "
            "Side effects were manageable and significantly lower than previous immunotherapies."
        ),
        "domain": "health",
        "source": "Nature Medicine",
    },
    {
        "title": "Electric Vehicle Sales Surpass 20% Global Market Share",
        "content": (
            "Global electric vehicle sales reached a new milestone in Q3, crossing 20% of all "
            "new car sales worldwide. China leads adoption at 40% EV market share, while Europe "
            "follows at 25% and the United States at 12%. "
            "Battery costs have fallen to below $80 per kilowatt-hour, making EVs cost-competitive "
            "with petrol vehicles in most markets. "
            "Major automakers announced accelerated plans to phase out internal combustion engines."
        ),
        "domain": "technology",
        "source": "Bloomberg NEF",
    },
    {
        "title": "Netflix Documentary on Deep-Sea Exploration Breaks Viewing Records",
        "content": (
            "Netflix premiered a new six-part documentary series following scientists aboard "
            "a research vessel exploring the Mariana Trench, the deepest point on Earth. "
            "The series captured previously unknown species at depths exceeding 10,000 metres, "
            "including bioluminescent jellyfish and translucent crustaceans never seen before. "
            "The documentary attracted 45 million viewers in its first week, making it the "
            "most-watched nature documentary in Netflix history."
        ),
        "domain": "entertainment",
        "source": "The Guardian",
    },
    {
        "title": "Quantum Computing Breakthrough: 1000-Qubit Processor Unveiled",
        "content": (
            "IBM unveiled a 1000-qubit quantum processor called 'Condor', pushing the boundaries "
            "of quantum advantage in practical applications. "
            "The chip demonstrates error correction at scale, a critical hurdle on the path "
            "to fault-tolerant quantum computing. "
            "Researchers demonstrated quantum advantage over classical supercomputers on specific "
            "optimisation and simulation tasks. "
            "IBM said commercial quantum cloud services using the new processor will be "
            "available to enterprise clients by 2025."
        ),
        "domain": "technology",
        "source": "IEEE Spectrum",
    },
    {
        "title": "Amazon Rainforest Records Lowest Deforestation in 15 Years",
        "content": (
            "Brazil's National Institute for Space Research reported that deforestation in the "
            "Amazon rainforest fell to its lowest level since 2008, declining 67% year-on-year. "
            "Stricter law enforcement, indigenous land protection programs, and satellite "
            "monitoring systems are credited with the dramatic reduction. "
            "Environmental scientists cautioned that the gains could be reversed without "
            "continued political commitment. "
            "The Amazon stores approximately 150 billion tonnes of carbon, making its "
            "preservation critical to global climate goals."
        ),
        "domain": "environment",
        "source": "AP News",
    },
    {
        "title": "Premier League: Manchester City Win Historic Fifth Consecutive Title",
        "content": (
            "Manchester City clinched their fifth consecutive Premier League title after a "
            "dramatic 3-2 comeback victory over Arsenal on the final day of the season. "
            "Erling Haaland finished as the league's top scorer with 38 goals, breaking his "
            "own single-season record. Manager Pep Guardiola said the achievement surpassed "
            "all previous accomplishments in his career. "
            "City's title win was confirmed when Liverpool failed to beat Chelsea at Stamford Bridge. "
            "The club are now the most decorated team in Premier League history."
        ),
        "domain": "sports",
        "source": "Sky Sports",
    },
    {
        "title": "Nuclear Fusion Milestone: Scientists Achieve Net Energy Gain Again",
        "content": (
            "Scientists at the National Ignition Facility achieved a net energy gain from "
            "nuclear fusion for the third consecutive time, generating 3.15 megajoules of "
            "energy from 2.05 megajoules of laser input — a gain ratio of 1.5x. "
            "Experts say the repeated success validates the viability of inertial confinement "
            "fusion as a future clean energy source. "
            "Several private companies announced new investments totalling $4 billion in "
            "fusion reactor development. Commercial fusion power may arrive by 2040."
        ),
        "domain": "science",
        "source": "Science Magazine",
    },
]


# ── Seed Function ─────────────────────────────────────────────────────────────

def seed():
    """
    Main seeding function.

    Steps:
        1. Create all DB tables
        2. Create admin user
        3. Create demo user
        4. Insert sample articles
        5. Generate SBERT embeddings for each article
        6. Save FAISS index to disk
    """
    logger.info("=" * 60)
    logger.info("Starting database seeding...")
    logger.info("=" * 60)

    # Step 1: Create tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables ready.")

    db = SessionLocal()

    try:
        # ── Step 2: Admin user ────────────────────────────────────────────────
        admin_email = "admin@newsplatform.com"
        admin_password = "Admin@1234"

        if not db.query(User).filter_by(email=admin_email).first():
            admin = User(
                name="Admin User",
                email=admin_email,
                hashed_password=hash_password(admin_password),
                role="admin",
            )
            db.add(admin)
            db.commit()
            logger.info("Admin created: %s / %s", admin_email, admin_password)
        else:
            logger.info("Admin user already exists. Skipping.")

        # ── Step 3: Demo user ─────────────────────────────────────────────────
        user_email = "user@newsplatform.com"
        user_password = "User@1234"

        if not db.query(User).filter_by(email=user_email).first():
            demo_user = User(
                name="Demo User",
                email=user_email,
                hashed_password=hash_password(user_password),
                role="user",
            )
            db.add(demo_user)
            db.commit()
            logger.info("Demo user created: %s / %s", user_email, user_password)
        else:
            logger.info("Demo user already exists. Skipping.")

        # ── Step 4: Articles ──────────────────────────────────────────────────
        existing_count = db.query(Article).count()
        if existing_count > 0:
            logger.info(
                "Articles already seeded (%d found). Skipping article insertion.",
                existing_count,
            )
        else:
            logger.info("Seeding %d articles...", len(SAMPLE_ARTICLES))

            emb_svc = get_embedding_service()
            faiss_svc = get_faiss_service()

            for i, article_data in enumerate(SAMPLE_ARTICLES, start=1):
                # Insert article into PostgreSQL
                article = Article(
                    title=article_data["title"],
                    content=article_data["content"],
                    domain=article_data["domain"],
                    source=article_data["source"],
                    embedding_generated=False,
                )
                db.add(article)
                db.commit()
                db.refresh(article)

                # Generate SBERT embedding
                combined_text = f"{article.title}. {article.content}"
                embedding = emb_svc.embed_text(combined_text)

                # Add to FAISS index
                faiss_svc.add(article.id, embedding)

                # Mark as embedded
                article.embedding_generated = True
                db.commit()

                logger.info(
                    "[%d/%d] ✓ %s",
                    i, len(SAMPLE_ARTICLES),
                    article.title[:60],
                )

            # Step 6: Save FAISS index to disk
            faiss_svc.save()
            logger.info(
                "FAISS index saved with %d vectors.",
                faiss_svc.total_vectors,
            )

        # ── Summary ───────────────────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("Seeding complete!")
        logger.info("  Articles : %d", db.query(Article).count())
        logger.info("  Users    : %d", db.query(User).count())
        logger.info("=" * 60)
        logger.info("Login credentials:")
        logger.info("  Admin : admin@newsplatform.com / Admin@1234")
        logger.info("  User  : user@newsplatform.com  / User@1234")
        logger.info("=" * 60)

    except Exception as exc:
        logger.error("Seeding failed: %s", exc)
        db.rollback()
        raise

    finally:
        db.close()


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    seed()