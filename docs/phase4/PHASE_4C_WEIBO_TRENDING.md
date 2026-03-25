# Phase 4c: Weibo-Trending Integration

## Status
⏳ Pending

## Skill Details
**Source**: ClawHub (`weibo-trending`)
**Purpose**: Weibo hot search data collection
**Status**: v1.0.0 ✅ (already published on ClawHub)

## Planned Features
- Multi-channel hot search (综合/社会/娱乐/生活)
- Real-time hot search collection (30 items per channel)
- Heat value and tags (热/新/商/官)
- SQLite persistence
- HTML visualization report
- Historical data query

## Integration Plan
1. Install from ClawHub
2. Create social sentiment pipeline
3. Integrate with sentiment_analyst
4. Extract investment signals from hot topics

## Installation Command
```bash
clawhub install weibo-trending
```

## Expected Timeline
Week 5-6

## Notes
- Weibo data is public and free
- Good for sentiment signals on Chinese stocks
- Legal risk is low (public data only)
