# Google Ads MCP Server - Deployment na elast.io

## Konfiguracja dla elast.io

### Build Command
```bash
docker-compose build
```

### Install Command
```bash
# Nie wymagane - wszystkie dependencies są instalowane w Dockerfile
echo "Dependencies installed during build"
```

### Run Command
```bash
docker-compose up
```

## Environment Variables (wymagane)

Ustaw następujące zmienne środowiskowe w panelu elast.io:

### **GOOGLE_PROJECT_ID** (wymagane)
- **Opis**: ID projektu Google Cloud
- **Przykład**: `my-google-cloud-project-123456`
- **Gdzie znaleźć**: Google Cloud Console -> Project Info

### **GOOGLE_ADS_DEVELOPER_TOKEN** (wymagane)
- **Opis**: Google Ads API Developer Token
- **Przykład**: `ABcdEFghIJklMNop` 
- **Gdzie zdobyć**: [Google Ads API Developer Token](https://developers.google.com/google-ads/api/docs/get-started/dev-token)

### **GOOGLE_CREDENTIALS_HOST_PATH** (wymagane)
- **Opis**: Ścieżka do pliku z credentials JSON na hoście
- **Wartość**: `./credentials.json`
- **Uwaga**: Plik credentials.json musi być dodany lokalnie (NIE do repo)

### **GOOGLE_ADS_LOGIN_CUSTOMER_ID** (opcjonalne)
- **Opis**: Customer ID manager account (jeśli używasz manager account)
- **Przykład**: `1234567890`
- **Kiedy użyć**: Gdy dostęp do customer account odbywa się przez manager account

## Reverse Proxy Configuration

- **Target**: `172.17.0.1:8888`
- **Protocol**: HTTP
- **Health Check Path**: `/health` (opcjonalne)

## Przygotowanie Credentials

1. **Wygeneruj Google Cloud Service Account JSON**:
   - Przejdź do Google Cloud Console
   - IAM & Admin -> Service Accounts
   - Utwórz nowy Service Account lub użyj istniejący
   - Wygeneruj klucz JSON
   - Dodaj scope: `https://www.googleapis.com/auth/adwords`

2. **Umieść plik credentials.json** w głównym katalogu projektu

3. **Alternatywnie**: Użyj Application Default Credentials
   ```bash
   gcloud auth application-default login \
     --scopes https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform \
     --client-id-file=YOUR_CLIENT_JSON_FILE
   ```

## Sprawdzanie Deploymentu

Po deployment sprawdź logi w panelu elast.io:
- Serwer powinien uruchomić się bez błędów
- Sprawdź połączenie z Google Ads API
- Testuj dostępność na porcie 8888

## Bezpieczeństwo

⚠️ **WAŻNE**: Nigdy nie commituj prawdziwych credentials do repozytorium!
- Użyj zmiennych środowiskowych
- Credentials.json dodaj do .gitignore
- Rozważ użycie Google Cloud Secret Manager