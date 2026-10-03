# Data Flow Diagram

{{HEADER:2 Marks}}

## Level 0 - Context Diagram

```
 ( User / Browser )                                          ( Google Gemini API )
        |   ^                                                      ^    |
        |   | plan, links, history                  prompt (+image)|    |JSON plan
        v   |                                                      |    v
   +--------------------------------------------------------------------------+
   |                       PocketSmart AI  (FastAPI)                           |
   +--------------------------------------------------------------------------+
        |   ^                                          |
        |   | users, plans                             | search-URL templates
        v   |                                          v
   [ SQLite: users, recommendations ]         ( Shopping platforms: Amazon, Flipkart,
                                                IKEA, Swiggy, Zomato, OYO ... )
```

## Level 1 - Main Processes

```
 ( User )
   | 1 credentials         | 2 budget form (+ image)        | 3 history request
   v                       v                                v
 +----------------+    +--------------------+         +------------------+
 | 1.0 Authenticate|   | 2.0 Validate Input |         | 5.0 Retrieve     |
 | (bcrypt + JWT)  |   | (Pydantic, image)  |         |     History      |
 +--------+-------+    +---------+----------+         +--------+---------+
      ^   |                      | valid input                 ^
      |   v JWT cookie           v                             | saved plans
  [ D1 users ]          +--------------------+  prompt (+image) |
                        | 3.0 Generate Plan  |----------> ( Gemini API )
                        | (model fallback,   |<----------  JSON plan
                        |  offline fallback) |                  |
                        +---------+----------+                  |
                                  | raw plan                    |
                                  v                             |
                        +--------------------+                  |
                        | 4.0 Validate Budget|                  |
                        | and Build Links    |                  |
                        +----+----------+----+                  |
                  final plan |          | save plan             |
                             v          v                       |
                      ( User: result ) [ D2 recommendations ]---+
```

| Symbol | Name | Meaning in this project |
|---|---|---|
| Oval ( ) | External entity | User, Google Gemini API, shopping platforms |
| Numbered box | Process | 1.0 Authenticate, 2.0 Validate Input, 3.0 Generate Plan, 4.0 Validate Budget and Links, 5.0 Retrieve History |
| [ ] | Data store | D1 users, D2 recommendations (SQLite) |
| Arrow | Data flow | Labeled on the diagram |
