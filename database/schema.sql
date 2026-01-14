CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS movies (
  id bigint PRIMARY KEY, -- TMDB id
  title text NOT NULL,
  release_date date,
  poster_path text,
  backdrop_path text,
  overview text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- decision: 1 = like, -1 = nope
CREATE TABLE IF NOT EXISTS swipes (
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  movie_id bigint NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
  decision smallint NOT NULL CHECK (decision IN (1, -1)),
  swiped_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, movie_id)
);

CREATE INDEX IF NOT EXISTS swipes_user_decision_idx ON swipes (user_id, decision);
