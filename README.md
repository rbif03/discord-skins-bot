# discord-skins-bot
A Discord bot that tracks Counter-Strike 2 skin prices, posts scheduled updates, and lets users manage tracked items via commands.  
Built with **Python**, **discord.py**, and the **Steam Web API**, backed by **AWS serverless** components.

# Contents
- [Gallery](#gallery)
- [Commands](#commands)
- [Architecture Overview](#architecture-overview)


## Gallery

<p align="center">
  <img width="696" height="265" alt="add_remove_skin" src="https://github.com/user-attachments/assets/f53ceea5-45e1-47da-9065-a85bf51eb321" />
</p>
<p align="center">
  <em>Example of the bot’s commands '->add_skin' and '->remove_skin'.</em>
</p>

---
 
<p align="center">
  <img width="434" height="331" alt="tracked_skins" src="https://github.com/user-attachments/assets/3f7cd588-561c-4c3d-90c8-1f3fe40c6ded" />
</p>
<p align="center">
  <em>Example of the bot’s '->tracked_skins' command.</em>
</p>

---


<p align="center">
  <img width="455" height="255" alt="image" src="https://github.com/user-attachments/assets/1eb43e41-1246-4454-92a5-5ca4187d60fe" />
</p>
<p align="center">
  <em>Example of the bot’s daily price update message in Discord.</em>
</p>

---





## Commands

### `->set_skinsbot_channel`
Sets the channel where SkinsBot will post price updates.  
**Required first step**: you won't get any price updates if you don't run this command.

---

### `->add_skin <skin name or Steam Market link>`
Start tracking a skin’s price.

You can provide:
- A properly formatted skin name (recommended), or  
- A full Steam Market listing link.

---

### `->remove_skin <skin name or Steam Market link>`
Stop tracking a previously added skin.

---

### `->tracked_skins`
Show all skins currently being tracked in this server/channel.

---

### `->formatting_help`
Displays examples and rules for correctly formatting skin names.  

---

### 💡 Tip

If a skin name isn’t being recognized, run: `->formatting_help`







## Architecture Overview

The system is composed of two main parts:

1. **The Bot**
2. **The Workers (Price Tracking Pipeline)**

This separation ensures reliability, scalability, and compliance with Steam API rate limits.

---

### 1. The Bot

The bot is the user-facing component of the system and runs entirely on **AWS Lambda**, making it fully **serverless**.

#### Why Lambda?

Lambda was chosen for **cost efficiency and simplicity**:

- The bot operates within the Lambda **free tier**, even on a paid account
- No servers to manage or maintain
- No always-on infrastructure costs

This significantly simplifies the architecture while keeping operational costs close to zero.

---

#### Execution Model

- The bot is triggered **every 15 minutes**
- During execution, it:
  - Connects to Discord
  - Handles user commands
  - Stores and updates tracked skins in the database

Before reaching the 15-minute timeout, the bot **gracefully shuts itself down**. This prevents overlapping executions and guarantees that only one bot instance is running at a time. Without this safeguard, concurrent Lambdas would cause commands to be processed multiple times.

As a result, the bot is briefly offline for approximately **30–40 seconds every 15 minutes**. This is an intentional trade-off: the application does not require constant availability, and short downtime is acceptable given the simplicity and cost benefits.

---

#### No Real-Time Price Fetching

The bot **does not fetch skin prices in real time**.

- User commands only define *what* skins should be tracked
- All Steam API calls are delegated to the Workers

This keeps the bot lightweight and avoids Steam API rate-limit issues caused by user-driven command flooding.

---

### 2. The Workers (Price Tracking Pipeline)

The Workers are responsible for fetching skin prices from the Steam API. They run once a day independently from the bot using **AWS Step Functions**, forming a controlled and rate-limited price tracking pipeline.

---

#### Workflow Overview

1. **Producer Step**
   - Fetches all tracked skins from the database
   - Aggregates tracked skins across all channels
   - Extracts the Steam market hash names to be tracked

2. **Map Execution**
   - Each hash name is processed individually
   - For each item:
     - A request is made to the Steam API to retrieve the current price
     - Execution respects API rate limits and timing constraints

3. **Persistence**
   - Retrieved prices are stored in a separate database table
   - This table is optimized for price history and lookups

---

#### Why This Architecture?

By moving all Steam API calls into a dedicated, asynchronous workflow:

- The bot remains fast and responsive
- API limits are respected
- Price tracking scales independently of user activity
- Failures in price fetching do not affect the bot itself
