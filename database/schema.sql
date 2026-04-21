create extension if not exists vector;

create table if not exists chunks (
    chunk_id bigserial primary key,
    doc_id text not null,
    chunk_text text not null,
    metadata jsonb default '{}'::jsonb,
    created_at timestamptz default now()
);

create table if not exists emb_openai_small (
    chunk_id bigint primary key references chunks(chunk_id) on delete cascade,
    embedding vector(1536),
    created_at timestamptz default now()
);

-- create table if not exists emb_openai_large (
--     chunk_id bigint primary key references chunks(chunk_id) on delete cascade,
--     embedding vector(3072),
--     created_at timestamptz default now()
-- );

create table if not exists emb_bge_base (
    chunk_id bigint primary key references chunks(chunk_id) on delete cascade,
    embedding vector(768),
    created_at timestamptz default now()
);

create table if not exists emb_bge_large (
    chunk_id bigint primary key references chunks(chunk_id) on delete cascade,
    embedding vector(1024),
    created_at timestamptz default now()
);

create index if not exists idx_openai_small_vec
on emb_openai_small
using hnsw (embedding vector_cosine_ops);

create index if not exists idx_bge_base_vec
on emb_bge_base
using hnsw  (embedding vector_cosine_ops);

create index if not exists idx_bge_large_vec
on emb_bge_large
using hnsw  (embedding vector_cosine_ops);

create index if not exists idx_chunks_doc_id
on chunks(doc_id);
create index if not exists idx_chunks_created
on chunks(created_at desc);