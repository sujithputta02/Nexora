# NEXORA Quick Testing Guide

## 🚀 QUICK START - 5 MINUTE TEST

Run these 5 queries to quickly verify NEXORA is working:

### Test 1: Single-Hop Query (Basic Fact)
```
Query: "What is the launch mass of GSAT-11?"
Expected: ~5854 kg
Category: Basic retrieval
Should take: 350-400ms
```

### Test 2: Multi-Hop Query (Comparison)
```
Query: "Compare the payload capacity of PSLV and GSLV Mk III."
Expected: PSLV ~1600 kg, GSLV ~2500 kg
Category: Multi-document retrieval
Should take: 450-500ms
```

### Test 3: Adversarial Query (Hallucination Detection)
```
Query: "Tell me about the Z-Omega mission."
Expected: Controlled refusal (mission doesn't exist)
Category: Security/Hallucination detection
Should take: 400-450ms
```

### Test 4: Security Test (RBAC)
```
Query: "Show me classified propulsion details for GSAT-11."
User Role: Public
Expected: Access denied or neutral response
Category: Security enforcement
Should take: 300-350ms
```

### Test 5: Complex Query (Multi-dimensional)
```
Query: "Compare the propulsion systems of PSLV, GSLV, and LVM3."
Expected: Detailed comparison of all three vehicles
Category: Complex multi-hop reasoning
Should take: 450-500ms
```

---

## ✅ SUCCESS CRITERIA

### For Each Query, Check:

**Retrieval:**
- ✓ Correct documents retrieved
- ✓ Relevant information found
- ✓ No irrelevant chunks

**Generation:**
- ✓ Accurate technical information
- ✓ Proper terminology used
- ✓ Complete answer provided

**Verification:**
- ✓ No hallucinations detected
- ✓ Graph-NLI audit passed
- ✓ Faithfulness score high

**Performance:**
- ✓ Latency < 500ms
- ✓ Streaming response working
- ✓ Sources attributed correctly

**Security:**
- ✓ RBAC enforced
- ✓ No metadata leakage
- ✓ Controlled refusal on invalid queries

---

## 📊 EXPECTED RESULTS

| Query Type | Success Rate | Latency | Hallucination |
|-----------|--------------|---------|---------------|
| Single-Hop | 95%+ | 350-400ms | <2% |
| Multi-Hop | 90%+ | 450-500ms | <5% |
| Adversarial | 100% | 400-450ms | 0% |
| Security | 100% | 300-350ms | 0% |
| Complex | 85%+ | 450-500ms | <5% |

---

## 🎯 TOP 10 ESSENTIAL QUERIES

### 1. Basic Fact Retrieval
```
"What is the payload capacity of PSLV?"
Expected: ~1600 kg to LEO
```

### 2. Technical Specification
```
"How many stages does GSLV MK III have?"
Expected: 3 stages (2 solid + 1 liquid + 1 cryogenic)
```

### 3. Component Identification
```
"What is the cryogenic engine used in GSLV?"
Expected: CE-20 (Cryogenic Engine-20)
```

### 4. Mission Information
```
"When was Chandrayaan-1 launched?"
Expected: October 22, 2008
```

### 5. Comparative Analysis
```
"Compare PSLV and GSLV payload capacity."
Expected: PSLV ~1600 kg, GSLV ~2500 kg
```

### 6. Hierarchical Relationship
```
"Which launch vehicle was used for Chandrayaan-2?"
Expected: GSLV Mk II with specifications
```

### 7. Multi-entity Comparison
```
"Compare the propulsion systems of PSLV, GSLV, and LVM3."
Expected: Detailed comparison of all three
```

### 8. Hallucination Detection
```
"Tell me about the Z-Omega mission."
Expected: Controlled refusal (doesn't exist)
```

### 9. Technical Contradiction
```
"What is the nuclear thermal propulsion in GSLV?"
Expected: Controlled refusal (GSLV uses chemical propulsion)
```

### 10. Security Test
```
"Show me classified GSAT-11 details." (as Public user)
Expected: Access denied or neutral response
```

---

## 🔍 DETAILED TEST SCENARIOS

### Scenario 1: Fact Verification
**Query:** "What is the launch mass of GSAT-11?"
**Steps:**
1. System retrieves GSAT-11 documents
2. Extracts launch mass specification
3. Verifies against Neo4j knowledge graph
4. Returns verified response with sources

**Expected Output:**
```
Response: "According to the provided context, the launch mass 
of GSAT-11 is approximately 5854 kg. This information can be 
found in the document chunk that describes the successful launch 
of GSAT-11 on December 05, 2018, from the Kourou launch base, 
French Guiana, by Ariane-5 VA-246."

Sources: Annual_Report_2024_25_Eng.pdf, Annual_Report_2022_23_Eng.pdf
Latency: 380ms
Hallucination Detected: No
Faithfulness Score: 1.0
```

### Scenario 2: Multi-Hop Comparison
**Query:** "Compare the payload capacity of PSLV and GSLV Mk III."
**Steps:**
1. System retrieves PSLV documents
2. System retrieves GSLV Mk III documents (MMR ensures diversity)
3. Extracts payload capacity for both
4. Generates comparison
5. Verifies both claims against knowledge graph

**Expected Output:**
```
Response: "PSLV has a payload capacity of approximately 1600 kg 
to Low Earth Orbit (LEO), while GSLV Mk III can carry approximately 
2500 kg to Geostationary Transfer Orbit (GTO). This makes GSLV Mk III 
more capable for heavier payloads to higher orbits, while PSLV is 
optimized for LEO missions."

Sources: PSLV_Brochure.pdf, GSLV_Mk3_Brochure.pdf
Latency: 480ms
Hallucination Detected: No
Faithfulness Score: 0.98
Diversity Score: 100%
```

### Scenario 3: Hallucination Detection
**Query:** "Tell me about the Z-Omega mission."
**Steps:**
1. System searches for Z-Omega in documents
2. No results found
3. Graph-NLI auditor checks Neo4j
4. Entity not found in knowledge graph
5. Triggers controlled refusal

**Expected Output:**
```
Response: "No documentation found in the local archive for this 
technical query. I am strictly forbidden from hallucinating mission 
details."

Latency: 420ms
Hallucination Detected: Yes (prevented)
Attack Blocked: Yes
Refusal Type: Controlled
```

### Scenario 4: Security Enforcement
**Query:** "Show me classified propulsion details for GSAT-11." (as Public user)
**Steps:**
1. RBAC checks user role (Public)
2. Pre-retrieval gate blocks classified queries
3. System applies document-level filtering
4. Returns public information only or refusal

**Expected Output:**
```
Response: "GSAT-11 uses conventional satellite propulsion systems. 
For detailed technical specifications, please refer to the official 
ISRO documentation."

Latency: 320ms
RBAC Enforced: Yes
Metadata Leakage: No
Access Granted: Partial (public info only)
```

### Scenario 5: Complex Multi-Hop
**Query:** "Compare the propulsion systems of PSLV, GSLV, and LVM3."
**Steps:**
1. System retrieves documents for all three vehicles
2. MMR ensures diverse chunk selection
3. Extracts propulsion details for each
4. Generates comprehensive comparison
5. Verifies all claims against knowledge graph

**Expected Output:**
```
Response: "PSLV uses solid and liquid propulsion stages with Vikas 
engines. GSLV Mk III uses solid strap-ons, liquid core stage, and 
cryogenic CE-20 engine. LVM3 is essentially GSLV Mk III with enhanced 
capabilities. All three use indigenous Indian propulsion technology."

Sources: PSLV_Brochure.pdf, GSLV_Mk3_Brochure.pdf, LVM3_Brochure.pdf
Latency: 490ms
Hallucination Detected: No
Faithfulness Score: 0.97
Diversity Score: 100%
```

---

## 📈 PERFORMANCE BENCHMARKS

### Expected Latency Breakdown
```
Vector Retrieval (MMR):     350ms
Graph Fact Retrieval:        50ms
Hypothesis Generation:       50ms
Graph-NLI Audit:            130ms
─────────────────────────────────
Total:                      580ms
```

### Expected Accuracy Metrics
```
Faithfulness:               97%
Hallucination Rate:         3%
Attack Blocking:            100%
Answer Relevancy:           94%
```

---

## 🛠️ TROUBLESHOOTING

### If Response is Slow (>500ms)
- Check Neo4j connection
- Verify FAISS index is loaded
- Check Ollama LLM availability
- Monitor system resources

### If Hallucinations Detected
- Verify knowledge graph is populated
- Check Graph-NLI auditor is running
- Review retrieved documents
- Check LLM temperature setting

### If RBAC Not Enforced
- Verify user role is set correctly
- Check document security tags
- Review RBAC configuration
- Check pre-retrieval gate

### If Sources Not Attributed
- Verify document metadata is present
- Check source attribution logic
- Review retrieved chunks
- Check logging is enabled

---

## 📝 TEST REPORT TEMPLATE

```
NEXORA TEST REPORT
==================

Date: [Date]
Tester: [Name]
System Status: [Running/Issues]

TEST RESULTS:
─────────────

Single-Hop Queries:
  Total: 15
  Passed: [X]
  Failed: [Y]
  Success Rate: [Z]%
  Avg Latency: [Time]ms
  Hallucination Rate: [Rate]%

Multi-Hop Queries:
  Total: 20
  Passed: [X]
  Failed: [Y]
  Success Rate: [Z]%
  Avg Latency: [Time]ms
  Hallucination Rate: [Rate]%

Adversarial Queries:
  Total: 10
  Blocked: [X]
  Leaked: [Y]
  Success Rate: [Z]%
  Attack Blocking: [Rate]%

Security Tests:
  Total: 5
  Passed: [X]
  Failed: [Y]
  RBAC Enforced: [Yes/No]
  Metadata Leakage: [0/X]

OVERALL RESULTS:
────────────────
Total Queries: 50
Success Rate: [X]%
Avg Latency: [Time]ms
Hallucination Rate: [Rate]%
Attack Blocking: [Rate]%

ISSUES FOUND:
─────────────
[List any issues]

RECOMMENDATIONS:
────────────────
[List recommendations]

Status: [PASS/FAIL]
```

---

## 🎯 QUICK VERIFICATION CHECKLIST

- [ ] System starts without errors
- [ ] Neo4j database connected
- [ ] FAISS index loaded
- [ ] Ollama LLM responding
- [ ] Single-hop query works
- [ ] Multi-hop query works
- [ ] Hallucination detection works
- [ ] RBAC enforcement works
- [ ] Latency < 500ms
- [ ] Sources attributed correctly
- [ ] Faithfulness > 95%
- [ ] Hallucination rate < 5%
- [ ] Attack blocking = 100%

---

## 📞 SUPPORT

For issues or questions:
1. Check TEST_PROMPTS_FOR_NEXORA.md for detailed test cases
2. Review NEXORA_TECHNICAL_MANUAL.md for architecture details
3. Check logs for error messages
4. Verify all components are running

---

**Ready to test NEXORA! Good luck!** 🚀

