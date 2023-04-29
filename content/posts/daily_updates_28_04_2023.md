---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2023-04-28
 linktitle: "Daily Update - 28th April 2023"
 title: "Daily Update: 28th April 2023"
 categories:
 - daily updates
 tags:
 - blog
 - updates
 type:
 - post
 - posts
 weight: 10
 series:
 - Weekly
 aliases:
 - /blog/daily-update-28-april-2023/
 toc: false
 comments: true
---

Started my day with talking to my family, and then kicking off work after getting ready. (Note: these blogs are mostly around my personal learning updates, so I'll mostly miss anything that I do at work as that's confidential)

1. [What is OSI Model | Real World Examples](https://www.youtube.com/watch?v=0y6FtKsg6J4)
    - Why this?
        - The answer to: "How does the communication work from client to server" is very important in backend. I wanted to see if I missed anything from my graduate studies, but nothing much. This was more like a refresher.
    - Notes:
        - Each operating system has their own implementation of TCP protocol. Linux has it's own for example, and it's open sourced.
        - Can take a look at TCP's source code in Linux source code to understand how checksum correction works.
    - Cloud load balancers: L4 Load Balancer (operates at TCP Level), L7 Load Balnacer (operates at Application Protocol Layer - HTTP/HTTPS)
2. [Postgres: Architectural Fundamentals](https://www.postgresql.org/docs/current/tutorial-arch.html)
    - Why this?
        - Going through database design and architectural fundamentals is helpful. I plan to explore CockroachDB soon, but wanted to get some idea about the ones I've used so far (Postgres for example)
    - Notes:
        - Uses client/server model.
        - PostgreSQL session consists following processes:
            - Server: manages DB files, accepts connections to the DB from client apps, performs DB actions on behalf of clients. DB server process is called postgres
            - Client (frontend): app that wants to perform DB operations.
        - Client/server could be on diff hosts: communicate over TCP/IP n/w connection
        - postgres can handle multiple connections from clients:
            - Forks a new process for each connection
                - The new process and client directly communicate
                - No intervention of postgres server
            - Supervisor server process is always running (daemon process), waiting for client connections
                - Client and child server process can come and go
3. [PostgreSQL System Architecture](https://www.geeksforgeeks.org/postgresql-system-architecture/)
    - Why this?
        - Just wanted to explore another blog on the same topic to see if I missed anything. Tbh, nothing much.
    - Notes:
        - PostgreSQL: process-per-transaction model
        - postgres server process:
            - Managed by postmaster, central coordinating process
            - Responsibilities:
                - Initializing, terminating the server
                - Handling connection requests from the new clients
                - Recovery
                - Run background processes
            - Shared Memory:
                - Reserved for DB caching and Transactional Log Caching
                - Shared Disk Buffer
                - Shared Tables
                    - Uses same set of tables to host multiple client data (TODO: how?)
        - Backend Processes:
            - Client interacts with backend processes (submits queries and receiving queries result)
            - Multiple backend servers executing queries concurrently
            - Each backend server:
                - will handle only a single query at a time
                - access data from main memory buffer pool (placed in shared memory)

Thank you! :) See y'all in the next blog.
