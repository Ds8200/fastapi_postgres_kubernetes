# מדריך פריסה מלא - Coordinates API עם Minikube

מדריך מפורט לפריסת האפליקציה על Minikube עם כל השלבים והבדיקות.

---

## שלב 1: הכנות ראשוניות

### בדיקת התקנות

```bash
# 1. בדוק ש-minikube מותקן
minikube version

# 2. התחל minikube (אם לא רץ)
minikube start

# 3. בדוק ש-kubectl מחובר ל-minikube
kubectl cluster-info

# 4. בדוק את ה-context הנוכחי
kubectl config current-context
# צריך להציג: minikube
```

**הסבר:** שלב זה מוודא ש-Minikube רץ וש-kubectl מוגדר נכון. אם minikube לא רץ, הפקודה `minikube start` תתחיל את הקלאסטר.

---

## שלב 2: עדכון שם התמונה ב-Deployment

**חשוב:** לפני בניית התמונה, עדכן את הקובץ `k8s/api/api-deployment.yaml` והחלף `<dockerhub_username>` בשם המשתמש שלך ב-Docker Hub.

**דוגמה:**
```yaml
image: yourusername/coordinates_api:v1
```

---

## שלב 3: בניית התמונה והעלאה ל-Docker Hub

### התחברות והגדרת סביבה

```bash
# 1. התחבר ל-Docker Hub
docker login

# 2. הגדר את Docker environment של minikube (חשוב!)
eval $(minikube docker-env)

# 3. בנה את התמונה
docker build -t <dockerhub_username>/coordinates_api:v1 .

# 4. דחוף ל-Docker Hub (אופציונלי - אם רוצה להשתמש ב-Docker Hub)
docker push <dockerhub_username>/coordinates_api:v1
```

**הסבר:**
- `docker login` - נדרש כדי לדחוף תמונות ל-Docker Hub
- `eval $(minikube docker-env)` - מגדיר את Docker להשתמש ב-Docker daemon של minikube, כך שהתמונות יהיו זמינות בקלאסטר
- אם לא דוחפים ל-Docker Hub, minikube ישתמש בתמונה המקומית

**הערה:** אם לא דוחפים ל-Docker Hub, ודא ש-minikube יכול לגשת לתמונה המקומית:
```bash
minikube image load <dockerhub_username>/coordinates_api:v1
```

---

## שלב 4: פריסת ConfigMap ו-Secret

### פריסת משאבי התצורה

```bash
# פרוס ConfigMap ו-Secret (חייב להיות לפני StatefulSet ו-Deployment)
kubectl apply -f k8s/db-configmap.yaml
kubectl apply -f k8s/db-secret.yaml

# בדוק שנוצרו
kubectl get configmap
kubectl get secret
```

**הסבר:**
- ConfigMap מכיל את משתני הסביבה הלא רגישים (POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER)
- Secret מכיל את הסיסמה (POSTGRES_PASSWORD)
- חייבים לפרוס אותם לפני StatefulSet ו-Deployment כי הם תלויים בהם

**פלט צפוי:**
```
NAME        DATA   AGE
db-config   4      5s

NAME          TYPE     DATA   AGE
db-secret     Opaque   1      5s
```

---

## שלב 5: פריסת PostgreSQL

### פריסת בסיס הנתונים

```bash
# 1. פרוס את PostgreSQL StatefulSet
kubectl apply -f k8s/postgres/postgres-statefulset.yaml

# 2. פרוס את PostgreSQL Service
kubectl apply -f k8s/postgres/postgres-service.yaml

# 3. בדוק את ה-StatefulSet
kubectl get statefulset

# 4. בדוק את ה-pods של PostgreSQL (יכול לקחת זמן)
kubectl get pods -l app=postgres

# 5. בדוק את ה-logs של pod אחד (אם יש בעיות)
kubectl logs postgres-0
```

**הסבר:**
- StatefulSet יוצר 3 pods של PostgreSQL עם אחסון קבוע
- Service יוצר headless service (ClusterIP: None) לזיהוי רשת יציב
- ה-pods יכולים לקחת זמן להתחיל, במיוחד ה-pods הראשונים

**פלט צפוי:**
```
NAME       READY   STATUS    RESTARTS   AGE
postgres-0 1/1     Running   0          30s
postgres-1 1/1     Running   0          25s
postgres-2 1/1     Running   0          20s
```

**אם יש בעיות:**
```bash
# בדוק את ה-logs
kubectl logs postgres-0

# בדוק את ה-describe
kubectl describe pod postgres-0
```

---

## שלב 6: פריסת ה-API

### פריסת האפליקציה

```bash
# 1. פרוס את ה-API Deployment
kubectl apply -f k8s/api/api-deployment.yaml

# 2. פרוס את ה-API Service
kubectl apply -f k8s/api/api-service.yaml

# 3. בדוק את ה-Deployment
kubectl get deployment

# 4. בדוק את ה-pods של ה-API
kubectl get pods -l app=coordinates-api

# 5. בדוק את ה-logs של pod אחד (אם יש בעיות)
kubectl logs <pod-name> -l app=coordinates-api
```

**הסבר:**
- Deployment יוצר 3 replicas של האפליקציה
- Service יוצר NodePort service על פורט 30080
- ה-pods צריכים להתחבר ל-PostgreSQL, אז ודא ש-PostgreSQL רץ לפני

**פלט צפוי:**
```
NAME             READY   UP-TO-DATE   AVAILABLE   AGE
coordinates-api  3/3     3            3           1m

NAME                              READY   STATUS    RESTARTS   AGE
coordinates-api-7d8f9c4b5-xxxxx   1/1     Running   0          30s
coordinates-api-7d8f9c4b5-yyyyy   1/1     Running   0          30s
coordinates-api-7d8f9c4b5-zzzzz   1/1     Running   0          30s
```

---

## שלב 7: בדיקות ואימות

### בדיקת כל המשאבים

```bash
# 1. בדוק את כל המשאבים
kubectl get all

# 2. בדוק את כל ה-pods וסטטוס
kubectl get pods

# 3. בדוק את ה-services
kubectl get svc

# 4. בדוק את ה-StatefulSet
kubectl get statefulset

# 5. בדוק את ה-Deployment
kubectl get deployment

# 6. בדוק את ה-ConfigMap
kubectl get configmap db-config -o yaml

# 7. בדוק את ה-Secret (הסיסמה תוצג ב-base64)
kubectl get secret db-secret -o yaml
```

**הסבר:**
- `kubectl get all` - מציג את כל המשאבים (pods, services, deployments, statefulsets)
- `kubectl get pods` - מציג את כל ה-pods עם הסטטוס שלהם
- `kubectl get svc` - מציג את כל ה-services

**פלט צפוי מ-`kubectl get all`:**
```
NAME                                  READY   STATUS    RESTARTS   AGE
pod/coordinates-api-xxx               1/1     Running   0          2m
pod/coordinates-api-yyy               1/1     Running   0          2m
pod/coordinates-api-zzz               1/1     Running   0          2m
pod/postgres-0                         1/1     Running   0          5m
pod/postgres-1                         1/1     Running   0          5m
pod/postgres-2                         1/1     Running   0          5m

NAME                         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/coordinates-api-svc  NodePort    10.96.xxx.xxx   <none>        8000:30080/TCP   2m
service/postgres-svc         ClusterIP   None            <none>        5432/TCP         5m

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/coordinates-api   3/3     3            3           2m

NAME                        READY   AGE
statefulset.apps/postgres   3/3     5m
```

---

## שלב 8: גישה לאפליקציה

### דרכים לגשת לאפליקציה

```bash
# אפשרות 1: שימוש ב-minikube service (פותח דפדפן)
minikube service coordinates-api-svc

# אפשרות 2: קבלת ה-URL
minikube service coordinates-api-svc --url

# אפשרות 3: שימוש ב-port-forward (אם צריך)
kubectl port-forward svc/coordinates-api-svc 30080:8000
```

**הסבר:**
- `minikube service` - פותח את השירות בדפדפן או מחזיר את ה-URL
- `port-forward` - מעביר פורט מקומית לקלאסטר (שימושי לבדיקות)

**פלט צפוי:**
```
http://192.168.49.2:30080
```

---

## שלב 9: בדיקת ה-API

### בדיקות פונקציונליות

```bash
# 1. קבל את ה-URL של השירות
SERVICE_URL=$(minikube service coordinates-api-svc --url)

# 2. בדוק health check
curl $SERVICE_URL/

# 3. הוסף קואורדינטה
curl -X POST $SERVICE_URL/coordinates \
  -H "Content-Type: application/json" \
  -d '{"latitude": 31.7683, "longitude": 35.2137, "name": "Jerusalem"}'

# 4. קבל את כל הקואורדינטות
curl $SERVICE_URL/coordinates

# 5. בדוק עם jq (אם מותקן) לעיצוב יפה
curl $SERVICE_URL/coordinates | jq .
```

**הסבר:**
- Health check - בודק שהאפליקציה רץ
- POST - מוסיף קואורדינטה חדשה
- GET - מקבל את כל הקואורדינטות

**פלט צפוי מ-health check:**
```json
{
  "status": "ok",
  "message": "Coordinates API is running"
}
```

**פלט צפוי מ-POST:**
```json
{
  "id": 1,
  "latitude": 31.7683,
  "longitude": 35.2137,
  "name": "Jerusalem"
}
```

**פלט צפוי מ-GET:**
```json
[
  {
    "id": 1,
    "latitude": 31.7683,
    "longitude": 35.2137,
    "name": "Jerusalem"
  }
]
```

---

## שלב 10: בדיקות מתקדמות

### בדיקות מעמיקות

```bash
# 1. בדוק את ה-logs של כל ה-pods
kubectl logs -l app=coordinates-api --tail=50

# 2. בדוק את ה-logs של PostgreSQL
kubectl logs postgres-0 --tail=50

# 3. בדוק describe של pod (אם יש בעיות)
kubectl describe pod <pod-name>

# 4. בדוק את ה-events
kubectl get events --sort-by='.lastTimestamp'

# 5. בדוק את ה-connectivity בין pods
kubectl exec -it <api-pod-name> -- ping postgres-svc
```

**הסבר:**
- `kubectl logs` - מציג את ה-logs של ה-pods
- `kubectl describe` - מציג מידע מפורט על pod (events, conditions, וכו')
- `kubectl get events` - מציג את כל ה-events בקלאסטר
- `kubectl exec` - מריץ פקודה בתוך pod

---

## שלב 11: צילומי מסך (למבחן)

### הכנת תמונות מסך לבדיקה

```bash
# 1. צילום מסך של kubectl get all
kubectl get all
# העתק את הפלט מהטרמינל ושמור כתמונה

# 2. צילום מסך של kubectl get pods
kubectl get pods -o wide
# העתק את הפלט ושמור כתמונה

# 3. צילום מסך של תגובת API
curl -X POST $SERVICE_URL/coordinates \
  -H "Content-Type: application/json" \
  -d '{"latitude": 40.7128, "longitude": -74.0060, "name": "New York"}'

curl $SERVICE_URL/coordinates
# העתק את הפלט ושמור כתמונה

# 4. פתח את ה-dashboard של minikube
minikube dashboard
# זה יפתח דפדפן עם ממשק גרפי - צלם מסך
```

**הסבר:**
- צילומי מסך נדרשים למבחן
- שמור את התמונות בתיקיית `screenshots/`
- שמות הקבצים: `kubectl-get-all.png`, `kubectl-get-pods.png`, `api-response.png`, `cluster-ui.png`

---

## פתרון בעיות נפוצות

### בעיות נפוצות ופתרונות

```bash
# אם pods לא מתחילים:
kubectl describe pod <pod-name>
# זה יציג את הסיבה לכשל

# אם יש בעיות image pull:
# ודא שהתמונה קיימת ב-Docker Hub או ב-minikube
minikube image ls

# אם יש בעיות חיבור ל-DB:
kubectl exec -it <api-pod-name> -- env | grep POSTGRES
# זה יציג את משתני הסביבה

# אם צריך למחוק הכל ולהתחיל מחדש:
kubectl delete -f k8s/
kubectl delete configmap db-config
kubectl delete secret db-secret

# אם minikube לא עובד:
minikube delete
minikube start
```

**בעיות נפוצות:**

1. **Pod במצב ImagePullBackOff:**
   - ודא שהתמונה קיימת ב-Docker Hub
   - או השתמש ב-`eval $(minikube docker-env)` לפני הבנייה

2. **Pod במצב CrashLoopBackOff:**
   - בדוק את ה-logs: `kubectl logs <pod-name>`
   - בדוק את ה-describe: `kubectl describe pod <pod-name>`

3. **בעיות חיבור ל-DB:**
   - ודא ש-PostgreSQL pods רצים: `kubectl get pods -l app=postgres`
   - בדוק את ה-ConfigMap: `kubectl get configmap db-config -o yaml`
   - ודא ש-POSTGRES_HOST הוא `postgres-svc`

4. **Service לא נגיש:**
   - בדוק את ה-service: `kubectl get svc coordinates-api-svc`
   - ודא ש-nodePort הוא 30080
   - נסה `minikube service coordinates-api-svc --url`

---

## סדר הפריסה המלא (פקודה אחת)

### פריסה מהירה של כל המשאבים

```bash
# פרוס הכל בסדר הנכון:
kubectl apply -f k8s/db-configmap.yaml && \
kubectl apply -f k8s/db-secret.yaml && \
kubectl apply -f k8s/postgres/postgres-statefulset.yaml && \
kubectl apply -f k8s/postgres/postgres-service.yaml && \
kubectl apply -f k8s/api/api-deployment.yaml && \
kubectl apply -f k8s/api/api-service.yaml && \
echo "All resources deployed!"
```

**הסבר:** פקודה זו מפריסה את כל המשאבים בסדר הנכון. אם אחד נכשל, הפקודות הבאות לא ירוצו.

---

## בדיקה מהירה שהכל עובד

### סקריפט בדיקה אוטומטי

```bash
#!/bin/bash

echo "=== Checking Pods ==="
kubectl get pods

echo -e "\n=== Checking Services ==="
kubectl get svc

echo -e "\n=== Testing API ==="
SERVICE_URL=$(minikube service coordinates-api-svc --url)
curl $SERVICE_URL/

echo -e "\n=== Adding Coordinate ==="
curl -X POST $SERVICE_URL/coordinates \
  -H "Content-Type: application/json" \
  -d '{"latitude": 31.7683, "longitude": 35.2137, "name": "Jerusalem"}'

echo -e "\n=== Getting All Coordinates ==="
curl $SERVICE_URL/coordinates
```

**שימוש:**
```bash
# שמור את הסקריפט כקובץ (למשל: test.sh)
chmod +x test.sh
./test.sh
```

---

## הערות חשובות

1. **ודא שהחלפת `<dockerhub_username>`** ב-`k8s/api/api-deployment.yaml` לפני הפריסה
2. **אם לא דוחפים ל-Docker Hub**, השתמש ב-`eval $(minikube docker-env)` לפני הבנייה
3. **חכה שה-pods יגיעו ל-`Running`** לפני בדיקת ה-API
4. **PostgreSQL StatefulSet יכול לקחת זמן** להתחיל (בעיקר ה-pods הראשונים)
5. **ודא ש-minikube רץ** לפני כל הפריסה: `minikube status`

---

## סיכום סדר הפעולות

1. ✅ בדוק ש-minikube רץ
2. ✅ עדכן את שם התמונה ב-`api-deployment.yaml`
3. ✅ בנה את התמונה עם `eval $(minikube docker-env)`
4. ✅ פרוס ConfigMap ו-Secret
5. ✅ פרוס PostgreSQL StatefulSet ו-Service
6. ✅ חכה ש-PostgreSQL pods רצים
7. ✅ פרוס API Deployment ו-Service
8. ✅ בדוק שהכל עובד
9. ✅ צלם מסך לבדיקה

---

**בהצלחה! 🚀**

