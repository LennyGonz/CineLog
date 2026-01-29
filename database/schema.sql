CREATE EXTENSION
IF NOT EXISTS "pgcrypto";

CREATE TABLE
IF NOT EXISTS users
(
  id uuid PRIMARY KEY DEFAULT gen_random_uuid
(),
  email text UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now
()
);

CREATE TABLE
IF NOT EXISTS genres
(
  id bigint PRIMARY KEY, -- TMDB genre id
  name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now
()
);

CREATE TABLE
IF NOT EXISTS movies
(
  id bigint PRIMARY KEY, -- TMDB id
  title text NOT NULL,
  release_date date,
  poster_path text,
  backdrop_path text,
  overview text,
  created_at timestamptz NOT NULL DEFAULT now
(),
  updated_at timestamptz NOT NULL DEFAULT now
()
);

-- Junction table for movies and genres
CREATE TABLE
IF NOT EXISTS movie_genres
(
  movie_id bigint NOT NULL REFERENCES movies
(id) ON
DELETE CASCADE,
  genre_id bigint
NOT NULL REFERENCES genres
(id) ON
DELETE CASCADE,
  PRIMARY KEY (movie_id, genre_id)
);

CREATE INDEX
IF NOT EXISTS movie_genres_genre_idx ON movie_genres
(genre_id);

-- decision: 1 = like, -1 = nope (used for old swipes table, keeping for backward compatibility)
CREATE TABLE
IF NOT EXISTS swipes
(
  user_id uuid NOT NULL REFERENCES users
(id) ON
DELETE CASCADE,
  movie_id bigint
NOT NULL REFERENCES movies
(id) ON
DELETE CASCADE,
  decision smallint
NOT NULL CHECK
(decision IN
(1, -1)),
  swiped_at timestamptz NOT NULL DEFAULT now
(),
  PRIMARY KEY
(user_id, movie_id)
);

CREATE INDEX
IF NOT EXISTS swipes_user_decision_idx ON swipes
(user_id, decision);

-- Master list: movies the user has seen and liked
CREATE TABLE
IF NOT EXISTS master_list
(
  user_id uuid NOT NULL REFERENCES users
(id) ON
DELETE CASCADE,
  movie_id bigint
NOT NULL REFERENCES movies
(id) ON
DELETE CASCADE,
  rating numeric(2, 1)
CHECK
(rating >= 0 AND rating <= 5), -- optional 0-5 star rating
  notes text,
  added_at timestamptz NOT NULL DEFAULT now
(),
  PRIMARY KEY
(user_id, movie_id)
);

CREATE INDEX
IF NOT EXISTS master_list_user_idx ON master_list
(user_id);

-- Watch later list: movies the user wants to see in the future
CREATE TABLE
IF NOT EXISTS watch_later_list
(
  user_id uuid NOT NULL REFERENCES users
(id) ON
DELETE CASCADE,
  movie_id bigint
NOT NULL REFERENCES movies
(id) ON
DELETE CASCADE,
  priority smallint
DEFAULT 1 CHECK
(priority BETWEEN 1 AND 5), -- 1=low to 5=high
  added_at timestamptz NOT NULL DEFAULT now
(),
  PRIMARY KEY
(user_id, movie_id)
);

CREATE INDEX
IF NOT EXISTS watch_later_user_idx ON watch_later_list
(user_id);

-- Friendships table (bidirectional)
CREATE TABLE
IF NOT EXISTS friendships
(
  user_id uuid NOT NULL REFERENCES users
(id) ON
DELETE CASCADE,
  friend_id uuid
NOT NULL REFERENCES users
(id) ON
DELETE CASCADE,
  status text
NOT NULL DEFAULT 'pending' CHECK
(status IN
('pending', 'accepted', 'blocked')),
  created_at timestamptz NOT NULL DEFAULT now
(),
  PRIMARY KEY
(user_id, friend_id),
  CONSTRAINT no_self_friendship CHECK
(user_id != friend_id)
);

CREATE INDEX
IF NOT EXISTS friendships_friend_idx ON friendships
(friend_id);
CREATE INDEX
IF NOT EXISTS friendships_status_idx ON friendships
(status);
