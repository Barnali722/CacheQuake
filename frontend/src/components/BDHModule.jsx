/**
 * BDHModule.jsx
 * Single responsibility: Render the dedicated BDH explainer step — comparing
 * our toy simulator's bdh_recurrent results (live) against BDH paper published
 * claims (precomputed), with mandatory PrecomputedBadge, per CONTROLS_SPEC §2.5.
 */

import React from 'react';
import PrecomputedBadge from './PrecomputedBadge';

// ─── Styles ──────────────────────────────────────────────────────────────────
const s = {
  wrapper: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    flexWrap: 'wrap',
  },
  title: { fontSize: '12px', color: '#e0e0f0', fontWeight: 600 },
  liveLabel: {
    display: 'inline-block',
    background: '#001f0f',
    border: '1px solid #3dffa0',
    color: '#3dffa0',
    fontSize: '10px',
    padding: '2px 8px',
    borderRadius: '3px',
  },
  colsGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '10px',
  },
  col: (live) => ({
    background: live ? '#0d120f' : '#120d00',
    border: `1px solid ${live ? '#3dffa0' : '#f5a623'}`,
    borderRadius: '6px',
    padding: '10px',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  }),
  colTitle: (live) => ({
    fontSize: '10px',
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
    color: live ? '#3dffa0' : '#f5a623',
    fontWeight: 600,
    marginBottom: '2px',
  }),
  stat: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '11px',
    color: '#aaaacc',
    borderTop: '1px solid rgba(255,255,255,0.05)',
    paddingTop: '5px',
    marginTop: '2px',
  },
  statVal: {
    color: '#e0e0f0',
    fontWeight: 600,
    fontFamily: 'monospace',
    fontSize: '12px',
  },
  mechDiagram: {
    background: '#0f0f14',
    border: '1px solid #2a2a3a',
    borderRadius: '6px',
    padding: '12px',
    fontSize: '11px',
    color: '#8888aa',
    lineHeight: 1.6,
  },
  mechTitle: {
    fontSize: '11px',
    color: '#c0c8ff',
    fontWeight: 600,
    marginBottom: '6px',
  },
  disclaimer: {
    fontSize: '10px',
    color: '#555',
    fontStyle: 'italic',
    borderTop: '1px solid #2a2a3a',
    paddingTop: '8px',
  },
  emptyNote: {
    fontSize: '11px',
    color: '#555',
  },
};

/**
 * BDHModule
 *
 * Props:
 *   liveStats         {object}  { cacheSizeTokens, accuracyScore } — from /simulate response
 *   publishedClaims   {object}  From data/precomputed/bdh_published_claims.json
 *
 * @see CONTROLS_SPEC.md §2.5
 */
function BDHModule({ liveStats = null, publishedClaims = null }) {
  const accuracy = liveStats?.accuracyScore != null
    ? `${Math.round(liveStats.accuracyScore * 100)}%`
    : '—';
  const cacheSize = liveStats?.cacheSizeTokens != null
    ? `${liveStats.cacheSizeTokens} tokens`
    : '—';

  return (
    <div id="bdh-module" style={s.wrapper} aria-label="BDH fixed-size recurrent state explainer">

      <div style={s.header}>
        <span style={s.title}>BDH Recurrent — Fixed-Size State</span>
      </div>

      {/* Two-column comparison: live (our toy) vs. published (paper) */}
      <div style={s.colsGrid}>

        {/* Left — live results from our simulator */}
        <div style={s.col(true)}>
          <div style={s.colTitle(true)}>Our toy simulator <span style={s.liveLabel}>LIVE</span></div>
          <div style={s.stat}>
            <span>Cache size</span>
            <span style={s.statVal}>{cacheSize}</span>
          </div>
          <div style={s.stat}>
            <span>Retrieval accuracy</span>
            <span style={s.statVal}>{accuracy}</span>
          </div>
          <div style={s.stat}>
            <span>Memory growth</span>
            <span style={{ ...s.statVal, color: '#3dffa0' }}>O(1) — flat</span>
          </div>
        </div>

        {/* Right — published claims (precomputed) */}
        <div style={s.col(false)}>
          <div style={s.colTitle(false)}>
            BDH paper
            {/* CONTROLS_SPEC §3 placement #2 — mandatory */}
            <PrecomputedBadge
              text="Published (arXiv:2509.26507) — not reproduced by our team"
              style={{ fontSize: '8px', padding: '1px 5px', marginLeft: '4px' }}
            />
          </div>
          {publishedClaims?.claims ? (
            publishedClaims.claims.map((c, i) => (
              <div key={i} style={s.stat}>
                <span>{c.label}</span>
                <span style={s.statVal}>{c.value}</span>
              </div>
            ))
          ) : (
            <div style={s.emptyNote}>
              Precomputed data not loaded yet — check /data/precomputed/bdh_published_claims.json
            </div>
          )}
        </div>
      </div>

      {/* BDH mechanism diagram / explanation */}
      <div style={s.mechDiagram}>
        <div style={s.mechTitle}>How BDH's fixed-size state works</div>
        <p style={{ margin: '0 0 6px' }}>
          Instead of appending a new row to a KV cache for every token, BDH maintains
          a fixed synaptic weight matrix <strong style={{ color: '#c0c8ff' }}>W</strong> of
          constant size. When a new key–value pair <em>(k, v)</em> arrives, it is written
          into <strong style={{ color: '#c0c8ff' }}>W</strong> by a local Hebbian update:
        </p>
        <div style={{
          fontFamily: 'monospace', fontSize: '12px', color: '#c084fc',
          background: '#1a1a28', borderRadius: '4px', padding: '6px 10px',
          margin: '4px 0',
        }}>
          W ← W + k·vᵀ (no append, no eviction — just overwrite)
        </div>
        <p style={{ margin: '6px 0 0', fontSize: '10px' }}>
          Reading is a matrix lookup: <code style={{ color: '#3dffa0' }}>v̂ = W·q</code>.
          Older associations are overwritten ("forgotten") by interference, not by eviction.
          This is why memory is O(1) — the state never grows.
        </p>
      </div>

      {/* Scale disclaimer */}
      <div style={s.disclaimer}>
        Our toy simulator demonstrates the O(1) memory property only. The BDH paper's
        published accuracy numbers are from a full-scale model — orders of magnitude
        larger than our toy. This comparison is illustrative, not quantitative.
      </div>

    </div>
  );
}

export default BDHModule;
