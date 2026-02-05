-- Database schema for Greenhouse candidates
-- Run this once to set up your database structure
-- Usage: psql greenhouse_candidates < schema.sql

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE SCHEMA IF NOT EXISTS gh;

CREATE TABLE IF NOT EXISTS gh.candidates (
  candidate_id        BIGINT PRIMARY KEY,

  -- Core identity
  first_name          TEXT,
  last_name           TEXT,
  full_name           TEXT,
  email               TEXT,
  phone_numbers       TEXT,     -- first phone or normalized single string
  addresses           TEXT,     -- first address or normalized single string

  -- Multi-valued fields – keep indexes aligned across arrays
  resume_links        TEXT[] NOT NULL DEFAULT '{}',
  resume_filenames    TEXT[] NOT NULL DEFAULT '{}',
  employment_titles   TEXT[] NOT NULL DEFAULT '{}',
  employment_companies TEXT[] NOT NULL DEFAULT '{}',
  degrees             TEXT[] NOT NULL DEFAULT '{}',
  jobs_name           TEXT[] NOT NULL DEFAULT '{}',

  -- Timestamps from Greenhouse
  created_at          TIMESTAMPTZ,
  updated_at          TIMESTAMPTZ,

  -- Raw for traceability
  raw                 JSONB NOT NULL
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_gh_candidates_email      ON gh.candidates (email);
CREATE INDEX IF NOT EXISTS idx_gh_candidates_updated_at ON gh.candidates (updated_at);
CREATE INDEX IF NOT EXISTS idx_gh_candidates_fullname_trgm
  ON gh.candidates USING gin (full_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_gh_candidates_resume_links_gin
  ON gh.candidates USING gin (resume_links);
CREATE INDEX IF NOT EXISTS idx_gh_candidates_resume_filenames_gin
  ON gh.candidates USING gin (resume_filenames);

-- Grant permissions (adjust as needed)
-- GRANT ALL ON SCHEMA gh TO chasepoulton;
-- GRANT ALL ON ALL TABLES IN SCHEMA gh TO chasepoulton;
