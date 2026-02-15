-- Staging: raw messages
select
  id,
  channel_id,
  external_id,
  text,
  created_at,
  processed_nlp
from {{ source('raw', 'messages') }}
where text is not null
