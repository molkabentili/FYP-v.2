Étude de l’existant, Problématique et Solutions
1. Étude de l’existant
Contexte Ooredoo Tunisie
Ooredoo est un des principaux opérateurs télécom en Tunisie, offrant des services mobiles, fixes et internet. L’entreprise propose à ses clients :
Forfaits prépayés et postpayés
Internet mobile et fixe
Offres combinées voix + data
Services pour entreprises (connectivité, cloud, IoT)
Méthodes actuelles de proposition d’offres
Les promotions et offres sont généralement générales, basées sur le type de contrat, l’ancienneté ou le profil client large.
Peu de personnalisation selon le comportement réel du client.
Les décisions marketing et de rétention sont principalement manuelles, basées sur des règles simples.
Limites et contraintes de l’existant
Churn élevé : certains clients quittent l’opérateur sans que l’on puisse l’anticiper.
Offres non personnalisées : des clients à risque peuvent recevoir des offres inadaptées.
Accessibilité des données : les données internes d’Ooredoo ne sont pas accessibles pour des projets académiques, ce qui nécessite l’utilisation de datasets publics pour des simulations réalistes.

2. Problématique
Dans le contexte actuel, Ooredoo ne dispose pas d’outils automatisés permettant :
de prédire le risque de churn pour chaque client,
d’adapter les offres en fonction du comportement réel des clients,
et de prioriser les actions de rétention.
Conséquences du problème :
Perte de revenus liée aux clients partants,
Offres mal ciblées,
Faible capacité à anticiper le départ des clients.
Résumé :
Il est nécessaire de disposer d’une plateforme capable d’analyser les données clients, d’évaluer le risque de churn et de faciliter la prise de décision pour la proposition d’offres adaptées.

3. Solutions proposées
Objectif du projet
Développer une plateforme de simulation et d’aide à la décision qui :
Analyse les données clients,
Prédit le churn à l’aide de modèles de machine learning simples,
Calcule un score de risque client (Low / Medium / High),
Détermine l’éligibilité des clients aux offres,
Présente les résultats via une interface web et des tableaux de bord interactifs.
Fonctionnalités principales
Analyse des données clients
Variables utilisées : tenure, type de contrat, facturation, méthode de paiement.
Les données simulées proviennent d’un dataset public (IBM Telco Customer Churn) pour remplacer les données internes non accessibles.
Prédiction du churn / évaluation du risque
Modèles simples adaptés à un projet Licence : Logistic Regression, Decision Tree, Random Forest.
Le churn sert de proxy pour le risque client.
Détermination de l’éligibilité aux offres
Basée sur le score de risque calculé.
Classes possibles : Eligible, Not Eligible, Retention Priority.
Interface web et tableaux de bord
Vue par client : informations clés, risque calculé, explication, décision sur les offres.
Dashboard global : distribution des risques, moyenne des probabilités de churn, pourcentage de clients éligibles aux offres.
Avantages de la solution
Permet de simuler des décisions réalistes sans utiliser de données internes confidentielles,
Fournit un outil académiquement solide illustrant le lien entre données clients, prédiction du churn et décisions marketing,
Accessible, explicable et adapté au niveau Licence.

