'use strict';

/**
 * In-memory cache. Replaces utils.js::logAndCache + globalCache export.
 *
 * RESIDUAL: per-process Map with no TTL, no eviction, no per-tenant scoping —
 * functionally equivalent to the original globalCache. Encapsulated here so
 * the v1.1 catalog addition (global-mutable-state -> dependency-injected
 * cache backend with TTL) has a single replacement point.
 */
class CacheService {
  constructor() { this._store = new Map(); }
  set(key, value) { this._store.set(key, value); }
  get(key) { return this._store.get(key); }
}

module.exports = CacheService;
