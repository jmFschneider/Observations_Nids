-- phpMyAdmin SQL Dump
-- version 5.2.1deb1
-- https://www.phpmyadmin.net/
--
-- Hôte : localhost:3306
-- Généré le : mer. 05 mars 2025 à 10:29
-- Version du serveur : 10.11.6-MariaDB-0+deb12u1
-- Version de PHP : 8.2.26

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `NidsObservation`
--

-- --------------------------------------------------------

--
-- Structure de la table `auth_group`
--

CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `auth_group_permissions`
--

CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `auth_permission`
--

CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can view log entry', 1, 'view_logentry'),
(5, 'Can add permission', 2, 'add_permission'),
(6, 'Can change permission', 2, 'change_permission'),
(7, 'Can delete permission', 2, 'delete_permission'),
(8, 'Can view permission', 2, 'view_permission'),
(9, 'Can add group', 3, 'add_group'),
(10, 'Can change group', 3, 'change_group'),
(11, 'Can delete group', 3, 'delete_group'),
(12, 'Can view group', 3, 'view_group'),
(13, 'Can add user', 4, 'add_user'),
(14, 'Can change user', 4, 'change_user'),
(15, 'Can delete user', 4, 'delete_user'),
(16, 'Can view user', 4, 'view_user'),
(17, 'Can add content type', 5, 'add_contenttype'),
(18, 'Can change content type', 5, 'change_contenttype'),
(19, 'Can delete content type', 5, 'delete_contenttype'),
(20, 'Can view content type', 5, 'view_contenttype'),
(21, 'Can add session', 6, 'add_session'),
(22, 'Can change session', 6, 'change_session'),
(23, 'Can delete session', 6, 'delete_session'),
(24, 'Can view session', 6, 'view_session'),
(25, 'Can add user', 7, 'add_user'),
(26, 'Can change user', 7, 'change_user'),
(27, 'Can delete user', 7, 'delete_user'),
(28, 'Can view user', 7, 'view_user'),
(29, 'Can add observation', 8, 'add_observation'),
(30, 'Can change observation', 8, 'change_observation'),
(31, 'Can delete observation', 8, 'delete_observation'),
(32, 'Can view observation', 8, 'view_observation'),
(33, 'Can add espece', 9, 'add_espece'),
(34, 'Can change espece', 9, 'change_espece'),
(35, 'Can delete espece', 9, 'delete_espece'),
(36, 'Can view espece', 9, 'view_espece'),
(37, 'Can add utilisateur', 10, 'add_utilisateur'),
(38, 'Can change utilisateur', 10, 'change_utilisateur'),
(39, 'Can delete utilisateur', 10, 'delete_utilisateur'),
(40, 'Can view utilisateur', 10, 'view_utilisateur'),
(41, 'Can add fiche observation', 11, 'add_ficheobservation'),
(42, 'Can change fiche observation', 11, 'change_ficheobservation'),
(43, 'Can delete fiche observation', 11, 'delete_ficheobservation'),
(44, 'Can view fiche observation', 11, 'view_ficheobservation'),
(45, 'Can add causes echec', 12, 'add_causesechec'),
(46, 'Can change causes echec', 12, 'change_causesechec'),
(47, 'Can delete causes echec', 12, 'delete_causesechec'),
(48, 'Can view causes echec', 12, 'view_causesechec'),
(49, 'Can add historique modification', 13, 'add_historiquemodification'),
(50, 'Can change historique modification', 13, 'change_historiquemodification'),
(51, 'Can delete historique modification', 13, 'delete_historiquemodification'),
(52, 'Can view historique modification', 13, 'view_historiquemodification'),
(53, 'Can add localisation', 14, 'add_localisation'),
(54, 'Can change localisation', 14, 'change_localisation'),
(55, 'Can delete localisation', 14, 'delete_localisation'),
(56, 'Can view localisation', 14, 'view_localisation'),
(57, 'Can add nid', 15, 'add_nid'),
(58, 'Can change nid', 15, 'change_nid'),
(59, 'Can delete nid', 15, 'delete_nid'),
(60, 'Can view nid', 15, 'view_nid'),
(61, 'Can add resume observation', 16, 'add_resumeobservation'),
(62, 'Can change resume observation', 16, 'change_resumeobservation'),
(63, 'Can delete resume observation', 16, 'delete_resumeobservation'),
(64, 'Can view resume observation', 16, 'view_resumeobservation'),
(65, 'Can add validation', 17, 'add_validation'),
(66, 'Can change validation', 17, 'change_validation'),
(67, 'Can delete validation', 17, 'delete_validation'),
(68, 'Can view validation', 17, 'view_validation');

-- --------------------------------------------------------

--
-- Structure de la table `auth_user`
--

CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `auth_user`
--

INSERT INTO `auth_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`) VALUES
(1, 'pbkdf2_sha256$870000$nTisphT1qqbyOkrUjlUEM6$GE8GYud4QdcdI1AfiQrZ/KI2KjZ8r0lPx4XYFcqkkkA=', '2025-03-04 18:13:17.660804', 1, 'jms', '', '', 'schneider.jm@free.fr', 1, 1, '2025-03-04 18:12:59.476765');

-- --------------------------------------------------------

--
-- Structure de la table `auth_user_groups`
--

CREATE TABLE `auth_user_groups` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `auth_user_user_permissions`
--

CREATE TABLE `auth_user_user_permissions` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `django_admin_log`
--

CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) UNSIGNED NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `django_admin_log`
--

INSERT INTO `django_admin_log` (`id`, `action_time`, `object_id`, `object_repr`, `action_flag`, `change_message`, `content_type_id`, `user_id`) VALUES
(1, '2025-03-04 18:26:10.151720', '1', 'Moineau domestique', 1, '[{\"added\": {}}]', 9, 1),
(2, '2025-03-04 18:26:23.656588', '1', 'Fiche 1 - 2025 (Moineau domestique)', 1, '[{\"added\": {}}]', 11, 1),
(3, '2025-03-04 21:31:06.058375', '1', 'Fiche 1 - 2025 (Moineau domestique)', 3, '', 11, 1);

-- --------------------------------------------------------

--
-- Structure de la table `django_content_type`
--

CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
(1, 'admin', 'logentry'),
(3, 'auth', 'group'),
(2, 'auth', 'permission'),
(4, 'auth', 'user'),
(5, 'contenttypes', 'contenttype'),
(12, 'Observations', 'causesechec'),
(9, 'Observations', 'espece'),
(11, 'Observations', 'ficheobservation'),
(13, 'Observations', 'historiquemodification'),
(14, 'Observations', 'localisation'),
(15, 'Observations', 'nid'),
(8, 'Observations', 'observation'),
(16, 'Observations', 'resumeobservation'),
(7, 'Observations', 'user'),
(10, 'Observations', 'utilisateur'),
(17, 'Observations', 'validation'),
(6, 'sessions', 'session');

-- --------------------------------------------------------

--
-- Structure de la table `django_migrations`
--

CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `django_migrations`
--

INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
(1, 'Observations', '0001_initial', '2025-03-03 21:07:32.231810'),
(2, 'contenttypes', '0001_initial', '2025-03-03 21:07:32.302049'),
(3, 'auth', '0001_initial', '2025-03-03 21:07:32.953158'),
(4, 'admin', '0001_initial', '2025-03-03 21:07:33.094545'),
(5, 'admin', '0002_logentry_remove_auto_add', '2025-03-03 21:07:33.103852'),
(6, 'admin', '0003_logentry_add_action_flag_choices', '2025-03-03 21:07:33.118587'),
(7, 'contenttypes', '0002_remove_content_type_name', '2025-03-03 21:07:33.245453'),
(8, 'auth', '0002_alter_permission_name_max_length', '2025-03-03 21:07:33.304292'),
(9, 'auth', '0003_alter_user_email_max_length', '2025-03-03 21:07:33.337548'),
(10, 'auth', '0004_alter_user_username_opts', '2025-03-03 21:07:33.352356'),
(11, 'auth', '0005_alter_user_last_login_null', '2025-03-03 21:07:33.407563'),
(12, 'auth', '0006_require_contenttypes_0002', '2025-03-03 21:07:33.414161'),
(13, 'auth', '0007_alter_validators_add_error_messages', '2025-03-03 21:07:33.422821'),
(14, 'auth', '0008_alter_user_username_max_length', '2025-03-03 21:07:33.460218'),
(15, 'auth', '0009_alter_user_last_name_max_length', '2025-03-03 21:07:33.491670'),
(16, 'auth', '0010_alter_group_name_max_length', '2025-03-03 21:07:33.522595'),
(17, 'auth', '0011_update_proxy_permissions', '2025-03-03 21:07:33.544936'),
(18, 'auth', '0012_alter_user_first_name_max_length', '2025-03-03 21:07:33.582433'),
(19, 'sessions', '0001_initial', '2025-03-03 21:07:33.658023'),
(20, 'Observations', '0002_espece_utilisateur_remove_observation_user_and_more', '2025-03-04 14:04:56.527671'),
(21, 'Observations', '0002_initial', '2025-03-05 10:21:14.114142');

-- --------------------------------------------------------

--
-- Structure de la table `django_session`
--

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `django_session`
--

INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
('vg2lw83qn4vb1of8hdhra2cfmoha8mjd', '.eJxVjEEOwiAQRe_C2hAYpFCX7nsGMsMwtmpKUtqV8e7apAvd_vfef6mE2zqmrZUlTawuyqrT70aYH2XeAd9xvlWd67wuE-ld0QdteqhcntfD_TsYsY3fuiPJcLYYewHvQQA8hx4zgEh0xE6cLRysEU9gUbpA7AuZkkkoGlHvD_ITOOc:1tpWlZ:wA1wsKw6gOr0mA8tekIGexA8Z8jNksP6wwfmmcTJwKs', '2025-03-18 18:13:17.676616');

-- --------------------------------------------------------

--
-- Structure de la table `Observations_causesechec`
--

CREATE TABLE `Observations_causesechec` (
  `id` bigint(20) NOT NULL,
  `description` longtext DEFAULT NULL,
  `fiche_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `Observations_espece`
--

CREATE TABLE `Observations_espece` (
  `id` bigint(20) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `commentaire` longtext DEFAULT NULL,
  `lien_oiseau_net` varchar(200) DEFAULT NULL,
  `valide_par_admin` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `Observations_espece`
--

INSERT INTO `Observations_espece` (`id`, `nom`, `commentaire`, `lien_oiseau_net`, `valide_par_admin`) VALUES
(1, 'Moineau domestique', '', 'https://www.oiseaux.net/oiseaux/moineau.domestique.html', 1);

-- --------------------------------------------------------

--
-- Structure de la table `Observations_ficheobservation`
--

CREATE TABLE `Observations_ficheobservation` (
  `id` bigint(20) NOT NULL,
  `num_fiche` varchar(50) NOT NULL,
  `annee` int(11) NOT NULL,
  `chemin_image` varchar(255) DEFAULT NULL,
  `espece_id` bigint(20) NOT NULL,
  `observateur_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `Observations_historiquemodification`
--

CREATE TABLE `Observations_historiquemodification` (
  `id` bigint(20) NOT NULL,
  `champ_modifie` varchar(100) NOT NULL,
  `ancienne_valeur` longtext NOT NULL,
  `nouvelle_valeur` longtext NOT NULL,
  `date_modification` datetime(6) NOT NULL,
  `observation_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `Observations_localisation`
--

CREATE TABLE `Observations_localisation` (
  `id` bigint(20) NOT NULL,
  `commune` varchar(100) NOT NULL,
  `departement` varchar(10) NOT NULL,
  `coordonnees` varchar(100) DEFAULT NULL,
  `altitude` varchar(10) DEFAULT NULL,
  `paysage` longtext DEFAULT NULL,
  `alentours` longtext DEFAULT NULL,
  `fiche_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `Observations_nid`
--

CREATE TABLE `Observations_nid` (
  `id` bigint(20) NOT NULL,
  `nid_prec_t_meme_couple` tinyint(1) NOT NULL,
  `hauteur_nid` int(11) DEFAULT NULL,
  `hauteur_couvert` int(11) DEFAULT NULL,
  `details_nid` longtext DEFAULT NULL,
  `fiche_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `Observations_observation`
--

CREATE TABLE `Observations_observation` (
  `id` bigint(20) NOT NULL,
  `heure` varchar(10) DEFAULT NULL,
  `jour` int(11) DEFAULT NULL,
  `mois` int(11) DEFAULT NULL,
  `nombre_oeufs` int(11) DEFAULT NULL,
  `nombre_poussins` int(11) DEFAULT NULL,
  `observations` longtext DEFAULT NULL,
  `fiche_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `Observations_resumeobservation`
--

CREATE TABLE `Observations_resumeobservation` (
  `id` bigint(20) NOT NULL,
  `premier_oeuf_pondu_jour` int(11) DEFAULT NULL,
  `premier_oeuf_pondu_mois` int(11) DEFAULT NULL,
  `premier_poussin_eclos_jour` int(11) DEFAULT NULL,
  `premier_poussin_eclos_mois` int(11) DEFAULT NULL,
  `premier_poussin_volant_jour` int(11) DEFAULT NULL,
  `premier_poussin_volant_mois` int(11) DEFAULT NULL,
  `nombre_oeufs_pondus` int(11) DEFAULT NULL,
  `nombre_oeufs_eclos` int(11) DEFAULT NULL,
  `nombre_oeufs_non_eclos` int(11) DEFAULT NULL,
  `nombre_poussins` int(11) DEFAULT NULL,
  `fiche_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `Observations_utilisateur`
--

CREATE TABLE `Observations_utilisateur` (
  `id` bigint(20) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `prenom` varchar(50) NOT NULL,
  `email` varchar(254) NOT NULL,
  `date_inscription` datetime(6) NOT NULL,
  `role` varchar(15) NOT NULL,
  `est_valide` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `Observations_utilisateur`
--

INSERT INTO `Observations_utilisateur` (`id`, `nom`, `prenom`, `email`, `date_inscription`, `role`, `est_valide`) VALUES
(1, 'Dupont', 'Jean', 'jean@example.com', '2025-03-04 18:16:36.477216', 'observateur', 0);

-- --------------------------------------------------------

--
-- Structure de la table `Observations_validation`
--

CREATE TABLE `Observations_validation` (
  `id` bigint(20) NOT NULL,
  `date_validation` datetime(6) NOT NULL,
  `observation_id` bigint(20) NOT NULL,
  `reviewer_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `auth_group`
--
ALTER TABLE `auth_group`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Index pour la table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  ADD KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`);

--
-- Index pour la table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`);

--
-- Index pour la table `auth_user`
--
ALTER TABLE `auth_user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Index pour la table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  ADD KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`);

--
-- Index pour la table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  ADD KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`);

--
-- Index pour la table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  ADD KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`);

--
-- Index pour la table `django_content_type`
--
ALTER TABLE `django_content_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`);

--
-- Index pour la table `django_migrations`
--
ALTER TABLE `django_migrations`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `django_session`
--
ALTER TABLE `django_session`
  ADD PRIMARY KEY (`session_key`),
  ADD KEY `django_session_expire_date_a5c62663` (`expire_date`);

--
-- Index pour la table `Observations_causesechec`
--
ALTER TABLE `Observations_causesechec`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `fiche_id` (`fiche_id`);

--
-- Index pour la table `Observations_espece`
--
ALTER TABLE `Observations_espece`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nom` (`nom`);

--
-- Index pour la table `Observations_ficheobservation`
--
ALTER TABLE `Observations_ficheobservation`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `num_fiche` (`num_fiche`),
  ADD KEY `Observations_ficheob_espece_id_f87d4ff5_fk_Observati` (`espece_id`),
  ADD KEY `Observations_ficheob_observateur_id_77755281_fk_Observati` (`observateur_id`);

--
-- Index pour la table `Observations_historiquemodification`
--
ALTER TABLE `Observations_historiquemodification`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Observations_histori_observation_id_6344b72c_fk_Observati` (`observation_id`);

--
-- Index pour la table `Observations_localisation`
--
ALTER TABLE `Observations_localisation`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `fiche_id` (`fiche_id`);

--
-- Index pour la table `Observations_nid`
--
ALTER TABLE `Observations_nid`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `fiche_id` (`fiche_id`);

--
-- Index pour la table `Observations_observation`
--
ALTER TABLE `Observations_observation`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Observations_observa_fiche_id_ab3214cf_fk_Observati` (`fiche_id`);

--
-- Index pour la table `Observations_resumeobservation`
--
ALTER TABLE `Observations_resumeobservation`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `fiche_id` (`fiche_id`);

--
-- Index pour la table `Observations_utilisateur`
--
ALTER TABLE `Observations_utilisateur`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Index pour la table `Observations_validation`
--
ALTER TABLE `Observations_validation`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Observations_validat_observation_id_09b8b0e0_fk_Observati` (`observation_id`),
  ADD KEY `Observations_validat_reviewer_id_a2492ad2_fk_Observati` (`reviewer_id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `auth_group`
--
ALTER TABLE `auth_group`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `auth_permission`
--
ALTER TABLE `auth_permission`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=69;

--
-- AUTO_INCREMENT pour la table `auth_user`
--
ALTER TABLE `auth_user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT pour la table `django_content_type`
--
ALTER TABLE `django_content_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT pour la table `django_migrations`
--
ALTER TABLE `django_migrations`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- AUTO_INCREMENT pour la table `Observations_causesechec`
--
ALTER TABLE `Observations_causesechec`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `Observations_espece`
--
ALTER TABLE `Observations_espece`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `Observations_ficheobservation`
--
ALTER TABLE `Observations_ficheobservation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `Observations_historiquemodification`
--
ALTER TABLE `Observations_historiquemodification`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `Observations_localisation`
--
ALTER TABLE `Observations_localisation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `Observations_nid`
--
ALTER TABLE `Observations_nid`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `Observations_observation`
--
ALTER TABLE `Observations_observation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT pour la table `Observations_resumeobservation`
--
ALTER TABLE `Observations_resumeobservation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `Observations_utilisateur`
--
ALTER TABLE `Observations_utilisateur`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `Observations_validation`
--
ALTER TABLE `Observations_validation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Contraintes pour la table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

--
-- Contraintes pour la table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  ADD CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Contraintes pour la table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Contraintes pour la table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  ADD CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Contraintes pour la table `Observations_causesechec`
--
ALTER TABLE `Observations_causesechec`
  ADD CONSTRAINT `Observations_causese_fiche_id_ef17440f_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`id`);

--
-- Contraintes pour la table `Observations_ficheobservation`
--
ALTER TABLE `Observations_ficheobservation`
  ADD CONSTRAINT `Observations_ficheob_espece_id_f87d4ff5_fk_Observati` FOREIGN KEY (`espece_id`) REFERENCES `Observations_espece` (`id`),
  ADD CONSTRAINT `Observations_ficheob_observateur_id_77755281_fk_Observati` FOREIGN KEY (`observateur_id`) REFERENCES `Observations_utilisateur` (`id`);

--
-- Contraintes pour la table `Observations_historiquemodification`
--
ALTER TABLE `Observations_historiquemodification`
  ADD CONSTRAINT `Observations_histori_observation_id_6344b72c_fk_Observati` FOREIGN KEY (`observation_id`) REFERENCES `Observations_observation` (`id`);

--
-- Contraintes pour la table `Observations_localisation`
--
ALTER TABLE `Observations_localisation`
  ADD CONSTRAINT `Observations_localis_fiche_id_38dd145c_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`id`);

--
-- Contraintes pour la table `Observations_nid`
--
ALTER TABLE `Observations_nid`
  ADD CONSTRAINT `Observations_nid_fiche_id_b11b0396_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`id`);

--
-- Contraintes pour la table `Observations_observation`
--
ALTER TABLE `Observations_observation`
  ADD CONSTRAINT `Observations_observa_fiche_id_ab3214cf_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`id`);

--
-- Contraintes pour la table `Observations_resumeobservation`
--
ALTER TABLE `Observations_resumeobservation`
  ADD CONSTRAINT `Observations_resumeo_fiche_id_30e7b36b_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`id`);

--
-- Contraintes pour la table `Observations_validation`
--
ALTER TABLE `Observations_validation`
  ADD CONSTRAINT `Observations_validat_observation_id_09b8b0e0_fk_Observati` FOREIGN KEY (`observation_id`) REFERENCES `Observations_observation` (`id`),
  ADD CONSTRAINT `Observations_validat_reviewer_id_a2492ad2_fk_Observati` FOREIGN KEY (`reviewer_id`) REFERENCES `Observations_utilisateur` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
