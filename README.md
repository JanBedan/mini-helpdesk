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








Problémy při tvorbě projektu a jejich řešení

Během realizace projektu se objevilo několik problémů:

1. Instalace Dockeru

Při instalaci Dockeru došlo k přerušení procesu (Ctrl+Z), což způsobilo zamknutí balíčkovacího systému (`apt lock`).
Řešení: dokončení rozpracované instalace pomocí `dpkg --configure -a` a následné opravení závislostí.



2. Problém s docker-compose

Při pokusu o spuštění aplikace pomocí `docker-compose` se objevila chyba (`KeyError: ContainerConfig`).
Řešení: místo docker-compose byl použit přímý způsob spuštění přes `docker build` a `docker run`.



3. Chyba při spuštění aplikace

Zpočátku nebylo jasné, který terminál slouží pro běh serveru a který pro testování.
Řešení: rozdělení práce na dva terminály – jeden pro běžící server, druhý pro testování pomocí `curl`.



4. Problém s Ollama (AI část)

Při volání endpointu `/ai` docházelo k chybě připojení (`connection refused`).
Příčina: Ollama nebyla spuštěná nebo nebyla dostupná z Docker kontejneru.

Řešení:

* instalace Ollama
* stažení modelu (`llama3.2:1b`)
* nastavení služby tak, aby byla dostupná i pro Docker (`OLLAMA_HOST=0.0.0.0`)



5. Konflikt portu Ollama

Při pokusu o spuštění Ollama se objevila chyba „address already in use“.
Řešení: zjištění, že služba již běží na pozadí a není potřeba ji spouštět znovu.



6. Problémy s GitHub přihlášením

Při nahrávání projektu na GitHub nebylo možné použít klasické heslo.
Řešení: vytvoření Personal Access Tokenu a jeho použití místo hesla.



7. Nastavení Git (email)

Došlo k nesprávnému nastavení emailu v Git konfiguraci.
Řešení: přepsání pomocí `git config --global user.email`.



8. Uložení projektu ve VirtualBoxu

Projekt byl vytvářen ve virtuálním stroji spuštěném z flash disku, hrozila ztráta dat.
Řešení: vytvoření zálohy projektu (ZIP) a uložení na flash disk.



Shrnutí

Většina problémů souvisela s konfigurací prostředí (Docker, Ollama, Git).
Po jejich vyřešení aplikace funguje správně a je dostupná přes síťový port.


