# Chess SQL Plugin

This plugin allows you to register and manage chess players, retrieve statistics, and query a SQLite database entirely through AI-generated SQL queries. It serves as a testbed for Cheshire Cat's capabilities in handling structured data efficiently.

<p align="center">
  <img src="https://raw.githubusercontent.com/shini161/chess-sql-plugin/3e074e53405e20afb973fb85099c14ce257297fa/assets/thumb.webp" 
       style="height: 512px; width: auto;">
</p>

## RoadMap
- [ ] `insert player (@forms)`
- [ ] `insert players \<count>{default=10} \<randomValues?>{default=true}`
- [ ] `get player count`
- [ ] `get player count`
- [ ] `get average [stat] \<filter>`
- [ ] `get min [stat] \<filter>`
- [ ] `get max [stat] \<filter>`
- [ ] `get players \<filter>`
- [ ] `clear table`
- [ ] `remove players <filter>`

## Installation

1. Clone the repository:
```Shell
git clone https://github.com/shini161/chess-sql-plugin.git
```

2. Copy the folder into the `/plugins` directory of your Cheshire Cat project:
```Shell
cp -r chess-sql-plugin /path/to/cheshire-cat/plugins/
```

3. Run your application:
```Shell
docker compose up
```

4. Enable the plugin and enjoy!
<img src="https://raw.githubusercontent.com/shini161/chess-sql-plugin/3e074e53405e20afb973fb85099c14ce257297fa/assets/enable_plugin_screen.png">

---

## Contributions

- **[shini161](https://github.com/shini161)**
- **[MatteoGhezza](https://github.com/MatteoGheza)**