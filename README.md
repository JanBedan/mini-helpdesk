Mini Helpdesk – síťová služba



Popis

Jednoduchá webová aplikace běžící v Docker kontejneru.
Aplikace poskytuje základní endpointy a jednoduchý AI výstup pomocí lokálního modelu (Ollama).



Síť

Aplikace běží na lokálním serveru (Ubuntu).
Komunikace probíhá přes TCP port 8081.



DNS

Pro projekt je použita doména ve tvaru:
jmenoprijmeni.skola.test

Doména slouží pro překlad na IP adresu serveru.



Aplikace

Aplikace běží v Docker kontejneru na portu 8081.



Endpointy:

GET /ping → vrací „pong“
GET /status → vrací JSON (stav, autor, čas)
POST /ai → vrací krátkou odpověď z lokálního LLM



Porty

TCP port: 8081



Spuštění

bash
docker build -t minihelpdesk .
docker run --name minihelpdesk -p 8081:8081 --add-host=host.docker.internal:host-gateway minihelpdesk



Testování



curl http://localhost:8081/ping
curl http://localhost:8081/status
curl -X POST http://localhost:8081/ai -H "Content-Type: application/json" -d "{\"prompt\":\"Co je DHCP?\"}"



AI (LLM)

Použit lokální model přes Ollama (běží na portu 11434).
Aplikace komunikuje s Ollamou přes její API.



Shrnutí

Aplikace běží v Docker kontejneru a je dostupná přes síťový port.
AI odpovědi jsou generovány lokálně pomocí LLM.

