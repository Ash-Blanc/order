# Roadmap

## TinyFish Hackathon Sprint

**Goal**: Demo-ready for HackerEarth pre-accelerator submission

**Timeline**: 2-3 weeks

---

## Phase 1: MVP Foundation (Week 1)

### Goal
Get core functionality working end-to-end.

### Tasks
- [ ] Backend runs without errors
- [ ] Frontend connects to backend
- [ ] One-Thing mode works
- [ ] Gather mode shows mock data
- [ ] Basic error handling
- [ ] README with setup instructions

### Acceptance Criteria
- `uv run uvicorn order.api:app` starts server
- `bun run dev` shows frontend
- Clicking through modes doesn't crash
- At least one commitment shows in One-Thing

### GitHub Issues
- #1 MVP Demo Ready
- #11 6 Modes End-to-End Testing

---

## Phase 2: Integrations + AI (Week 1-2)

### Goal
Real data flowing from sources, AI working.

### Tasks
- [ ] TinyFish API key configuration
- [ ] Discord gatherer with real account
- [ ] X (Twitter) gatherer with real account
- [ ] GitHub gatherer with real PAT
- [ ] Gmail gatherer with real account
- [ ] Test AI synthesis quality
- [ ] Add fallback mode

### Acceptance Criteria
- All 4 sources show as connected
- Gather pulls real commitments
- AI filters noise correctly
- Works without LLM API key

### GitHub Issues
- #2 Source Integrations
- #10 AI Synthesis Quality

---

## Phase 3: Polish + Pitch (Week 2)

### Goal
Production-ready for demo, compelling pitch.

### Tasks
- [ ] Improve mode selector UX
- [ ] Add loading states
- [ ] Add animations/transitions
- [ ] Error states with retry
- [ ] Empty states
- [ ] Source icons
- [ ] Deadline indicators
- [ ] Create pitch deck (8-10 slides)
- [ ] Record demo video (60-90s)

### Acceptance Criteria
- Feels like a polished product
- Pitch deck ready
- Demo video uploaded

### GitHub Issues
- #3 Frontend Polish
- #4 Pitch Deck
- #5 Demo Video

---

## Phase 4: Deployment (Week 2-3)

### Goal
Live demo URL for judges.

### Tasks
- [ ] Deploy backend to Railway/Fly.io
- [ ] Deploy frontend to Vercel
- [ ] Set environment variables
- [ ] Test all endpoints
- [ ] Add deployment badges

### Acceptance Criteria
- Live URL works
- All API endpoints accessible
- Frontend connects to backend

### GitHub Issues
- #6 Deployment

---

## Hackathon Submission Checklist

- [ ] Working demo (live URL or video)
- [ ] Pitch deck (PDF)
- [ ] Demo video (60-90s)
- [ ] Code repository (public)
- [ ] README with setup
- [ ] TinyFish integration prominent

---

## Post-Hackathon Roadmap

### Phase 5: Production Ready
- Rate limiting
- Input validation
- Proper CORS
- Error logging
- Health monitoring
- **Issue #7 Security**

### Phase 6: Quality of Life
- Email digests
- Mobile responsive polish
- Keyboard shortcuts
- Better error messages
- **Issue #8 Email Digest**

### Phase 7: Scale
- Multi-user support
- Team workspaces
- Shared commitments
- Integrations (Slack, Teams)
- Webhooks

### Phase 8: Intelligence
- Better AI extraction
- Deadline prediction
- Commitment patterns
- Smart reminders
- Priority learning

---

## Success Metrics

### Hackathon
- ✅ Demo works live
- ✅ Pitch deck compelling
- ✅ TinyFish integration shown
- ✅ All 6 modes functional

### Post-Hackathon
- Real users actually using it
- Commitments gathered per week
- Time saved vs manual organization
- User retention

---

## Timeline Visualization

```
Week 1          Week 2          Week 3
├───────────────┼───────────────┼───────────────┤
│ Phase 1       │ Phase 3       │ Phase 4       │
│ MVP           │ Polish        │ Deploy        │
│               │               │               │
│ Phase 2       │ Phase 3       │ SUBMISSION    │
│ Integrations  │ Pitch/Video   │               │
└───────────────┴───────────────┴───────────────┘
```

---

## What We're NOT Doing

- ❌ Mobile app (web first)
- ❌ Multi-user (personal tool first)
- ❌ Team features (solo first)
- ❌ Manual entry (pull only)
- ❌ Another methodology (zero setup)

---

## The Focus

**MVP → Demo → Submit → Iterate**

Get it working. Get it to judges. Get feedback. Build more.

*"We got no users so no need to worry about old things"* — Ash-Blanc
