# Protocols for Digital Peacebuilding: A Governance Framework for AI-Assisted Constitution Drafting in Syria

## Abstract

This paper presents **Algorithmic Consensus**, a technical framework for inclusive deliberation in post-conflict Syria. The system adapts the Polis/vTaiwan model -- proven in Taiwan's digital democracy with an 80% policy implementation rate -- for contexts where traditional participation barriers (illiteracy, security fears, displacement, dialect diversity) exclude the most affected populations from constitution-building processes. The framework uses voice-first AI (Whisper ASR for Syrian Arabic dialects), unsupervised machine learning (PCA + K-Means clustering on vote matrices), and bridge statement detection to transform qualitative narratives into quantifiable consensus metrics. Critically, the system is designed with anti-hallucination safeguards: no generative AI produces deliberation content. AI observes and measures; humans speak and decide.

---

## 1. Introduction

### 1.1 The Participation Gap

Post-conflict constitution drafting in Syria faces a structural paradox: the populations most affected by conflict -- internally displaced persons, women in camps, elderly non-literate citizens -- are systematically excluded from the processes meant to protect them. The barriers are multilayered:

- **Literacy barriers**: An estimated 2.4 million Syrian children have been out of school for over a decade. Adults in displacement camps frequently lack the written literacy required for text-based surveys or online consultations.
- **Security fears**: Participation in political discussions carries real physical risk. Anonymous digital participation removes the link between identity and opinion.
- **Dialect fragmentation**: Syrian Arabic dialects (Damascene, Aleppine, Coastal, Bedouin) vary significantly. Formal consultation documents in Modern Standard Arabic (MSA) alienate speakers of colloquial dialects.
- **Digital access inequality**: While smartphone penetration in camps is surprisingly high (via WhatsApp and voice messaging), digital literacy for text-based platforms remains low.

The result: constitution-drafting tables are dominated by urban, educated, politically connected elites whose priorities may diverge significantly from the broader population.

### 1.2 The Polis/vTaiwan Precedent

Taiwan's vTaiwan platform demonstrated that technology can bridge this gap. Using the open-source Polis system, vTaiwan facilitated large-scale deliberation on contentious policy issues (ride-sharing regulation, alcohol sales, telecom regulation) with the following results:

- **28+ cases** processed through the digital deliberation pipeline
- **80% implementation rate**: four in five cases led to decisive government action
- **Thousands of participants** per consultation, far exceeding traditional town halls

The Polis mechanism achieves this through a deceptively simple design:

1. Participants submit short statements (<140 characters)
2. Others vote: agree, disagree, or pass
3. **No direct replies are permitted** (eliminates trolling and flame wars)
4. An unsupervised algorithm clusters participants by voting patterns
5. **Bridge statements** are identified: ideas that receive strong agreement from opposing clusters
6. These bridges form the foundation for policy recommendations

This paper adapts this proven model for the Syrian context, adding voice-first input, Arabic NLP, and geographic concern mapping.

### 1.3 Why Not Just Use Polis Directly?

Polis is an excellent tool, but its design assumes:
- Text literacy for both submission and consumption
- English or well-supported Latin-script languages for NLP features
- Participants comfortable with web-based interfaces

None of these assumptions hold in displacement camps in Idlib, rural Aleppo, or cross-border refugee communities. Our framework extends the Polis model rather than replacing it.

---

## 2. System Architecture

### 2.1 Three-Pillar Design

```
INPUT LAYER (Pillar 1)          PROCESSING LAYER (Pillar 2)       OUTPUT LAYER (Pillar 3)
───────────────────────         ──────────────────────────         ─────────────────────────
Voice → Whisper ASR             Vote Matrix Construction          Unity Score
   or                          Column-Mean Imputation            Consensus Index
Text → Validation               PCA → 2D Projection               Fear Heatmap
   ↓                            K-Means Clustering                Policy Report
Embedding (768-dim)             Bridge Statement Detection
Sentiment Analysis
   ↓                                ↓                                ↓
[SQLite Database — models.py — Anonymous Storage]
```

### 2.2 Technology Choices

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Speech-to-text | OpenAI Whisper (base) | Supports Arabic, handles Syrian dialect acceptably, runs locally (no cloud dependency) |
| Embeddings | paraphrase-multilingual-mpnet-base-v2 | Best-quality multilingual embeddings, strong Arabic support, 768 dimensions |
| Sentiment | CAMeL-Lab arabert | Purpose-built for Arabic, MIT license, offline-capable |
| Clustering | scikit-learn (PCA + KMeans) | Industry-standard, well-documented, deterministic with fixed seed |
| Storage | SQLite | Zero-configuration, embedded, no server needed (critical for field deployment) |
| Privacy | UUID-based anonymous IDs | No PII stored. Location is optional, city-level only (never GPS coordinates) |

### 2.3 Anti-Hallucination Architecture

A central design concern is ensuring that AI enhances rather than distorts democratic deliberation. The following safeguards are embedded at every layer:

| Layer | Safeguard | Implementation |
|-------|-----------|---------------|
| Input | Human-only authoring | Whisper transcribes verbatim. No paraphrasing, summarizing, or "cleaning" of participant text. |
| Input | Character limit | 140-character enforcement prevents manipulation through lengthy, persuasive text. |
| Processing | Math-only analysis | The clustering algorithm operates on vote integers (-1, 0, 1) and numpy arrays. No language model is invoked. |
| Processing | No generated labels | Clusters are labeled generically ("Group A", "Group B"), never with AI-generated descriptions that could frame groups. |
| Output | No generated summaries | Reports present raw human statements (verbatim) alongside computed numerical scores. |
| Entire pipeline | No LLM in deliberation loop | The only AI models used are: Whisper (transcription), sentence-transformers (similarity measurement), camel-tools (sentiment classification). None generate text that enters the deliberation. |

**Governing principle: AI observes and measures; humans speak and decide.**

---

## 3. Methodology

### 3.1 Input Collection

Participants interact through one of two channels:

**Voice input**: Participants send audio messages (e.g., via WhatsApp voice notes or recorded .wav files). Whisper ASR transcribes the Arabic audio to text. The `language="ar"` parameter forces Arabic decoding, preventing misidentification of Syrian dialect as Turkish or Persian (a known Whisper failure mode without language forcing).

**Text input**: Participants type statements directly. Both channels feed into the same validation pipeline: whitespace trimming, empty-string rejection, 140-character enforcement.

Each statement receives two metadata computations:
- **Semantic embedding** (768-dimensional vector via sentence-transformers): captures meaning for potential future deduplication
- **Sentiment classification** (positive/negative/neutral via camel-tools arabert): used in geographic fear mapping

### 3.2 Deliberation Mechanics

The deliberation follows the Polis model:

1. **Statement submission**: Any participant can submit a statement (voice or text, <140 chars)
2. **Voting**: Each participant sees statements (in randomized order) and votes agree, disagree, or pass
3. **No direct replies**: Participants cannot respond to or comment on specific statements. This is a deliberate design choice that prevents:
   - Trolling and personal attacks
   - Rhetorical domination by articulate speakers
   - Echo chambers formed by threaded discussions
4. **Anonymity**: Participants are identified only by anonymous UUIDs. Statement authorship is stored but never displayed.

### 3.3 The Clustering Algorithm

**Step 1: Vote Matrix Construction**

Let P = number of participants, S = number of statements (with sufficient votes).
Construct matrix M ∈ ℝ^(P×S) where:
- M[i][j] = 1 if participant i agrees with statement j
- M[i][j] = -1 if participant i disagrees
- M[i][j] = 0 if participant i passes
- M[i][j] = NaN if participant i has not voted on statement j

**Step 2: Missing Vote Imputation**

For each column j (statement):
- μⱼ = mean of all non-NaN values in column j
- Replace each NaN in column j with μⱼ

This column-mean imputation assumes a non-voter would have voted similarly to the average. This is the same approach used by the original Polis system. Note: if vote coverage drops below 30%, the imputed values become unreliable and the system issues a warning.

**Step 3: PCA Dimensionality Reduction**

Apply Principal Component Analysis to project the P-dimensional vote vectors into 2D:

X_projected = PCA(n_components=2).fit_transform(M_imputed)

The two principal components capture the axes of maximum variance in voting patterns. After projection, participants who vote similarly cluster together in 2D space.

The explained_variance_ratio_ from PCA indicates what fraction of total voting pattern information is preserved in the 2D projection. Values above 0.5 suggest the 2D view captures the majority of opinion structure.

**Step 4: K-Means Clustering**

For k ∈ {2, 3, 4, 5}:
1. Run K-Means(n_clusters=k) on the 2D projections
2. Compute silhouette score s(k)

Select k* = argmax s(k).

The silhouette score measures cluster separation quality:
- s ≈ 1.0: clusters are tight and well-separated
- s ≈ 0.0: clusters overlap (no clear grouping)
- s < 0: assignment errors (unusual with K-Means)

**Step 5: Bridge Statement Detection**

For each statement j:
- For each cluster c:
  - agreement_rate(j, c) = |{votes from c where value = 1}| / |{all votes from c on j}|
- clusters_agreeing(j) = |{c : agreement_rate(j, c) ≥ 0.60}|
- If clusters_agreeing(j) ≥ 2:
  - Statement j is a **bridge statement**
  - bridge_score(j) = mean({agreement_rate(j, c) : agreement_rate(j, c) ≥ 0.60})

Bridge statements are ranked by bridge_score descending. These represent the actionable consensus.

### 3.4 Consensus Metrics

**Unity Score** = |bridge statements| / |total statements|

Interpretation:
- < 0.10: Deep polarization
- 0.10 - 0.25: Some common ground emerging
- 0.25 - 0.50: Strong consensus
- > 0.50: Verify participant diversity (possible echo chamber)

**Consensus Index** = Σ(wᵦ × scoreᵦ) / Σ(wᵦ) for all bridge statements b

where wᵦ = clusters_agreeing(b) / total_clusters

This weights bridges by how many groups they span. A statement uniting all 4 clusters carries more weight than one uniting 2.

**Fear Heatmap**: Cross-tabulation of negative-sentiment statements by participant location and opinion cluster, visualized as a color-intensity matrix. Reveals geographic patterns in community concerns.

---

## 4. Privacy and Ethical Considerations

### 4.1 Privacy-by-Design

- **No Personally Identifiable Information (PII)** is collected or stored
- Participants are assigned random UUID-based anonymous identifiers
- Location is optional, self-reported, and stored only at city granularity (never GPS coordinates)
- The database (SQLite) is a single local file, not cloud-hosted, meaning data never leaves the deployment environment
- Statement authorship is stored for audit but never displayed to other participants or in reports

### 4.2 Algorithmic Resistance

The question "How do we prevent manipulation?" is critical in a conflict context. Safeguards include:

**Sybil resistance**: In a production deployment, participant registration would be tied to verified phone numbers (one participant per number) to prevent vote stuffing. The prototype uses UUID generation without verification.

**Coordinated voting detection**: The clustering algorithm itself exposes coordinated behavior. A group of bots voting identically will form an anomalously tight cluster that can be flagged and investigated.

**Statement flooding prevention**: The 140-character limit and moderation queue (for production) prevent any single actor from dominating the statement pool.

**Transparency**: All algorithmic parameters (bridge threshold, cluster count, PCA dimensions) are configurable and documented. No black-box decisions are made.

### 4.3 Limitations and Honest Caveats

- **Small-sample clustering instability**: With fewer than 30 participants, K-Means on 2D projections can produce meaningless clusters. The system warns when N < 10 but ideally needs 50+ participants for robust analysis.
- **Whisper dialect accuracy**: The `base` Whisper model handles MSA well but Syrian colloquial Arabic less reliably. Field deployment would require dialect-adapted fine-tuning.
- **Sentiment model bias**: The arabert sentiment model was trained primarily on MSA text. Syrian dialect expressions of fear, anger, or hope may be misclassified.
- **Selection bias**: The system cannot address who participates, only how they participate. A deliberation dominated by urban smartphone users will not represent rural populations. Deployment strategy (field facilitators, community outreach) is as important as the technology.
- **No causal claims**: The system identifies correlation in voting patterns and surfaces areas of agreement. It does not explain *why* groups agree or what policy mechanisms would address their concerns.

---

## 5. Feasibility Study Design

### 5.1 Proposed Pilot

A feasibility study with 500 Syrian participants across diverse backgrounds:

| Segment | Target N | Recruitment Channel |
|---------|----------|-------------------|
| Damascus residents | 100 | Local community centers |
| Aleppo residents | 100 | Local community centers |
| Idlib residents | 100 | Field facilitators |
| Refugee communities (Lebanon/Turkey) | 100 | UNHCR partnerships |
| Diaspora | 100 | Online recruitment |

### 5.2 Protocol

1. **Registration**: Participant receives anonymous ID via facilitator or self-registration
2. **Orientation**: 5-minute voice tutorial explaining: submit ideas, vote on others' ideas, no replies
3. **Deliberation window**: 4 weeks (following vTaiwan's timeline)
4. **Topic prompt**: "What is the single most important thing for Syria's future that everyone should agree on?"
5. **Data collection**: Statements, votes, timestamps, optional location
6. **Analysis**: Run the Algorithmic Consensus pipeline at days 7, 14, 21, 28 to track consensus evolution

### 5.3 Success Criteria

- ≥ 60% of participants submit at least 1 statement and cast at least 10 votes
- Vote coverage ≥ 30%
- ≥ 3 bridge statements identified with bridge_score ≥ 0.65
- PCA explained variance ≥ 0.40 (meaningful opinion structure exists)
- Silhouette score ≥ 0.30 (clusters are distinguishable)

---

## 6. Deployment Recommendations

### 6.1 vTaiwan-Style Four-Stage Integration

Following the proven vTaiwan model:

**Stage 1 - Proposal**: Government or civil society identifies a specific constitutional question (e.g., "How should property rights be handled for displaced persons?")

**Stage 2 - Online Deliberation**: Deploy Algorithmic Consensus for 4 weeks. Collect statements and votes. Identify bridge statements and opinion clusters.

**Stage 3 - Face-to-Face Consultation**: Convene representative stakeholders (from each identified cluster) to discuss the bridge statements in person. Use the fear heatmap to ensure geographic concerns are addressed.

**Stage 4 - Legislative Translation**: Draft constitutional language based on bridge statements with documented cross-group agreement percentages.

### 6.2 Technical Requirements for Field Deployment

- **Server**: Single Linux server with 8GB RAM, GPU optional (CPU inference acceptable for <1000 participants)
- **Connectivity**: System designed for intermittent connectivity. SQLite is local; sync can happen when connection is available.
- **Facilitators**: Trained field workers who can help non-literate participants record voice messages and understand the voting process
- **Languages**: System supports Arabic (MSA + dialects via Whisper). Kurdish and Turkmen support would require additional ASR models.

---

## 7. Conclusion

The Algorithmic Consensus framework demonstrates that AI can serve democracy without replacing human judgment. By combining voice-first input (making participation accessible), Polis-style deliberation mechanics (surfacing common ground), and transparent quantitative metrics (making consensus measurable), the system offers a concrete protocol for inclusive constitution-building in post-conflict contexts.

The framework's anti-hallucination architecture -- ensuring AI only measures, never speaks -- is not merely a technical safeguard but a political one. In a context where trust has been destroyed by years of propaganda and manipulation, a system that transparently shows "these are YOUR words, and this is how much you agree with each other" has a fundamentally different legitimacy than one where an AI summarizes, interprets, or generates.

The bridge statements surfaced by this system are not AI-generated compromises. They are human ideas that, through the arithmetic of cross-cluster agreement, reveal the common ground that already exists but is invisible through the fog of polarization.

---

## References

- Hsiao, Y. T., Lin, S. Y., Tang, A., Narayanan, D., & Sarahe, C. (2018). vTaiwan: An Empirical Study of Open Consultation Process in Taiwan. SocArXiv.
- Small, C., Bjorkegren, M., Erkkilä, T., Shaw, L., & Megill, C. (2021). Polis: Scaling Deliberation by Mapping High Dimensional Opinion Spaces. Recerca.
- OpenAI. (2024). Democratic Inputs to AI Grant Program Update. openai.com.
- Radford, A., Kim, J. W., Xu, T., Brockman, G., McLeavey, C., & Sutskever, I. (2022). Robust Speech Recognition via Large-Scale Weak Supervision. arXiv:2212.04356.
- Obeid, O., Zalmout, N., Khalifa, S., Taji, D., Erdmann, A., Habash, N. (2020). CAMeL Tools: An Open Source Python Toolkit for Arabic Natural Language Processing.

---

*This paper accompanies the Algorithmic Consensus prototype implementation.*
*System version: 0.1 | AI observes and measures; humans speak and decide.*
