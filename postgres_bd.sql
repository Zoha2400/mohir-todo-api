CREATE DATABASE mohirtodo;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    uid UUID DEFAULT gen_random_uuid() UNIQUE,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    age INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    creator UUID REFERENCES users(uid) ON DELETE CASCADE,
    project_uid UUID DEFAULT gen_random_uuid() UNIQUE,
    description VARCHAR(500)
);


CREATE TABLE todos(
    id SERIAL PRIMARY KEY,
    todo_project UUID REFERENCES projects(project_uid) ON DELETE CASCADE,
    text VARCHAR(250) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status BOOLEAN DEFAULT FALSE,
    creator UUID REFERENCES users(uid) ON DELETE CASCADE,
)
