-- phpMyAdmin SQL Dump
-- version 5.2.1deb1
-- https://www.phpmyadmin.net/
--
-- Hôte : localhost:3306
-- Généré le : sam. 22 mars 2025 à 08:08
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
(25, 'Can add espece', 7, 'add_espece'),
(26, 'Can change espece', 7, 'change_espece'),
(27, 'Can delete espece', 7, 'delete_espece'),
(28, 'Can view espece', 7, 'view_espece'),
(29, 'Can add utilisateur', 8, 'add_utilisateur'),
(30, 'Can change utilisateur', 8, 'change_utilisateur'),
(31, 'Can delete utilisateur', 8, 'delete_utilisateur'),
(32, 'Can view utilisateur', 8, 'view_utilisateur'),
(33, 'Can add fiche observation', 9, 'add_ficheobservation'),
(34, 'Can change fiche observation', 9, 'change_ficheobservation'),
(35, 'Can delete fiche observation', 9, 'delete_ficheobservation'),
(36, 'Can view fiche observation', 9, 'view_ficheobservation'),
(37, 'Can add causes echec', 10, 'add_causesechec'),
(38, 'Can change causes echec', 10, 'change_causesechec'),
(39, 'Can delete causes echec', 10, 'delete_causesechec'),
(40, 'Can view causes echec', 10, 'view_causesechec'),
(41, 'Can add Historique de modification', 11, 'add_historiquemodification'),
(42, 'Can change Historique de modification', 11, 'change_historiquemodification'),
(43, 'Can delete Historique de modification', 11, 'delete_historiquemodification'),
(44, 'Can view Historique de modification', 11, 'view_historiquemodification'),
(45, 'Can add localisation', 12, 'add_localisation'),
(46, 'Can change localisation', 12, 'change_localisation'),
(47, 'Can delete localisation', 12, 'delete_localisation'),
(48, 'Can view localisation', 12, 'view_localisation'),
(49, 'Can add nid', 13, 'add_nid'),
(50, 'Can change nid', 13, 'change_nid'),
(51, 'Can delete nid', 13, 'delete_nid'),
(52, 'Can view nid', 13, 'view_nid'),
(53, 'Can add observation', 14, 'add_observation'),
(54, 'Can change observation', 14, 'change_observation'),
(55, 'Can delete observation', 14, 'delete_observation'),
(56, 'Can view observation', 14, 'view_observation'),
(57, 'Can add resume observation', 15, 'add_resumeobservation'),
(58, 'Can change resume observation', 15, 'change_resumeobservation'),
(59, 'Can delete resume observation', 15, 'delete_resumeobservation'),
(60, 'Can view resume observation', 15, 'view_resumeobservation'),
(61, 'Can add validation', 16, 'add_validation'),
(62, 'Can change validation', 16, 'change_validation'),
(63, 'Can delete validation', 16, 'delete_validation'),
(64, 'Can view validation', 16, 'view_validation'),
(65, 'Can add historique validation', 17, 'add_historiquevalidation'),
(66, 'Can change historique validation', 17, 'change_historiquevalidation'),
(67, 'Can delete historique validation', 17, 'delete_historiquevalidation'),
(68, 'Can view historique validation', 17, 'view_historiquevalidation'),
(69, 'Can add remarque', 18, 'add_remarque'),
(70, 'Can change remarque', 18, 'change_remarque'),
(71, 'Can delete remarque', 18, 'delete_remarque'),
(72, 'Can view remarque', 18, 'view_remarque');

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
(1, 'pbkdf2_sha256$870000$sbYqGXoyBXhpkNLKmhAKKy$3uKwWbxTeeqgxT2pEZCG2oiPVoOD3XffdTWhtpMgZQM=', '2025-03-11 13:25:46.144329', 1, 'jms', '', '', 'schneider.jm@free.fr', 1, 1, '2025-03-07 20:42:20.556717');

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
  `user_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `django_admin_log`
--

INSERT INTO `django_admin_log` (`id`, `action_time`, `object_id`, `object_repr`, `action_flag`, `change_message`, `content_type_id`, `user_id`) VALUES
(2, '2025-03-12 17:43:38.435733', '5', 'toto albi (Observateur)', 1, '[{\"added\": {}}]', 8, 3),
(3, '2025-03-13 13:56:29.294068', '3', 'Jean-Marie Schneider (Administrateur)', 2, '[{\"changed\": {\"fields\": [\"First name\", \"Last name\", \"Role\", \"Est valide\"]}}]', 8, 3);

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
(10, 'Observations', 'causesechec'),
(7, 'Observations', 'espece'),
(9, 'Observations', 'ficheobservation'),
(11, 'Observations', 'historiquemodification'),
(17, 'Observations', 'historiquevalidation'),
(12, 'Observations', 'localisation'),
(13, 'Observations', 'nid'),
(14, 'Observations', 'observation'),
(18, 'Observations', 'remarque'),
(15, 'Observations', 'resumeobservation'),
(8, 'Observations', 'utilisateur'),
(16, 'Observations', 'validation'),
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
(1, 'Observations', '0001_initial', '2025-03-07 20:39:59.726190'),
(2, 'contenttypes', '0001_initial', '2025-03-07 20:39:59.795158'),
(3, 'auth', '0001_initial', '2025-03-07 20:40:00.506560'),
(4, 'admin', '0001_initial', '2025-03-07 20:40:00.650022'),
(5, 'admin', '0002_logentry_remove_auto_add', '2025-03-07 20:40:00.668865'),
(6, 'admin', '0003_logentry_add_action_flag_choices', '2025-03-07 20:40:00.681747'),
(7, 'contenttypes', '0002_remove_content_type_name', '2025-03-07 20:40:00.809269'),
(8, 'auth', '0002_alter_permission_name_max_length', '2025-03-07 20:40:00.873751'),
(9, 'auth', '0003_alter_user_email_max_length', '2025-03-07 20:40:00.921810'),
(10, 'auth', '0004_alter_user_username_opts', '2025-03-07 20:40:00.921810'),
(11, 'auth', '0005_alter_user_last_login_null', '2025-03-07 20:40:00.985639'),
(12, 'auth', '0006_require_contenttypes_0002', '2025-03-07 20:40:00.985639'),
(13, 'auth', '0007_alter_validators_add_error_messages', '2025-03-07 20:40:01.001566'),
(14, 'auth', '0008_alter_user_username_max_length', '2025-03-07 20:40:01.049252'),
(15, 'auth', '0009_alter_user_last_name_max_length', '2025-03-07 20:40:01.098852'),
(16, 'auth', '0010_alter_group_name_max_length', '2025-03-07 20:40:01.144935'),
(17, 'auth', '0011_update_proxy_permissions', '2025-03-07 20:40:01.177524'),
(18, 'auth', '0012_alter_user_first_name_max_length', '2025-03-07 20:40:01.224971'),
(19, 'sessions', '0001_initial', '2025-03-07 20:40:01.300932'),
(20, 'Observations', '0002_alter_causesechec_description_and_more', '2025-03-08 14:17:13.362704'),
(21, 'Observations', '0003_remarque', '2025-03-09 19:45:09.661301'),
(22, 'Observations', '0004_remove_observation_nom', '2025-03-10 17:30:47.611303'),
(23, 'Observations', '0005_alter_utilisateur_options_alter_utilisateur_managers_and_more', '2025-03-12 15:46:02.685614'),
(24, 'Observations', '0006_remove_utilisateur_date_inscription_and_more', '2025-03-12 16:00:02.932965'),
(25, 'Observations', '0007_remove_utilisateur_date_inscription_and_more', '2025-03-13 22:32:10.612261'),
(26, 'Observations', '0008_remove_utilisateur_date_inscription_and_more', '2025-03-21 15:22:43.517085');

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
('1vc9mvqkoyv34tljita010md1iqj8lh0', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttDV4:rJalYvY_tdVzoKmRhI6WrSy8o6yIM7K4-wL6ck2GxmI', '2025-03-14 23:27:30.440155'),
('2pmjcdn9wze8fco716qv8rrxf9svk97p', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttQcm:yAZg-mAu2_Z1TSgXntGOMA8f6C4-4ZWa-KcGHBfI3d8', '2025-03-15 13:28:20.801029'),
('30wj308pr9pzvc55yp35755oq1nh6er8', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tuc3w:5vKnqvWbJKrGA1wAEP8Vdh7feS8nGE309PcoikIEtEE', '2025-03-18 19:53:16.581947'),
('3fgvkcq8335v5b6jldyfbfzf2gx05yer', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvJti:60W-ClgfX7KbmMKyDi3AfNDSh8tjZThHUFoqqyJj6sk', '2025-03-20 18:41:38.589475'),
('4noobv3t27tj8uv5ldcraiz9syfgcx0v', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tsr9F:8Ha5soWwBKlSd1SydAC2yLko5FXeSqmWbRAjrHmvln8', '2025-03-13 23:35:29.148052'),
('7l0k9eu4oarfa0ztdd348syoshuvdl8i', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tt8Td:FwWUWz-WR6IEgyL7CCjvmWJiFzlpYEiJUhr04pQ0bNY', '2025-03-14 18:05:41.508244'),
('81l1kvy06ibw45gnzn17ws869646wsyj', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttoya:aG46Q3Kf6Xn7ZBXJCoHxZJ-Goblwn_FXIHjtBT1pxYE', '2025-03-16 15:28:28.599120'),
('8yhtjj2ozogkgi0n4pqe3dsd6o6zzl7j', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tsow9:2TlAXoI64PGzsrWGlEWLDJqvoHauKszHyXR0QN34tyU', '2025-03-13 21:13:49.601782'),
('91s0f0bgf0eijn6i9pcfi5nyfb9v9swq', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvkt7:Dl1c83Fp9NshCgnc6lxX7CExT7kqA_ee0jU8m4bJJwY', '2025-03-21 23:30:49.819055'),
('b13oiondmyfnkpttorm9g814hc6sxhtw', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttYdL:AWnBCmGMiPnbBDbrcfygQ81UGex1ojGk_Y_Hy0c-7vo', '2025-03-15 22:01:27.175559'),
('b7i8ni7hb7yjcu8l4dxgfpn99v1fho94', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvNdR:oximmrvv7Csz6DEkD25_78QR63eubKHP3GBUgsik0dY', '2025-03-20 22:41:05.870419'),
('c9ow7wo2vddccg53vbh6yy2s3y4lkprq', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttVgF:m-sfMmICS9XBKJeRnWDlb6zyf7_Xg35SBGKTtY2ffeA', '2025-03-15 18:52:15.564043'),
('cyhe9r6ei3357q689920bf23jh4pzki7', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvdO3:xlgjewHMUnbh4ome7JgvqqG22S4boOa7R1KW1iQIJhA', '2025-03-21 15:30:15.278510'),
('da167v0uz91yyfx0dq3v9lhoxuis7ifh', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttN5C:ex-Byp3Hpq6XzSTZGJAXmKr3HUl7scUqB5C5TL_UpwI', '2025-03-15 09:41:26.614067'),
('dlsqaezic6yamx9dncso16plfmxd1mze', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvafw:1BNltQ8dQvDhNpLdw7mUsbmy4R-N0iRBWe3O_88jVgE', '2025-03-21 12:36:32.452576'),
('etz3nh5w935vivhkn2cfj77e90is961t', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tviC9:cbLxz_COI7O8Qy5TyAza3gvISRjGCyBqgglUEZRTgJM', '2025-03-21 20:38:17.356979'),
('gd8phqtbwq9kteeeb7siru330vji635n', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvYyw:jfYvQNxIg963vS3aWVcz8tQ8dGhHv022YFFfBMP3Hz8', '2025-03-21 10:48:02.220374'),
('gdipcwu7kcdxmv7xajb6ry4jdx9z0d55', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttvdg:UYcyvb4ghqDgxXE7hh-I16r8QfxoHfAKPXYuTDMlYLw', '2025-03-16 22:35:20.821030'),
('gtddmcca0dkbu3vey2qvlclefwe561we', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttWeV:BHpg41aRIEKgXlGpZs7RrZfBjY5qjv5ce_IZ0FC_XjY', '2025-03-15 19:54:31.336106'),
('gxn5dv4wjv9ty9sfxkc4alfvwdbnfzc7', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvBNI:BFtAENMrj3LUoN2irOcGsXzYDJ1XKd9_lstBoE6YTyk', '2025-03-20 09:35:36.717178'),
('hvhsdpwmui8vgsohrrd9snvstqa3jey9', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvM6Q:kFiImRrhf1a60epcHpcmxP9Ea32sO6zYbjJd2vtscDg', '2025-03-20 21:02:54.792521'),
('j3kppsravfrrmnbjoa8xq9oy20fnehez', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tuxsZ:HkeRIu5coVwIoqB-wrWjs98wHbYW3zvLmZxuonJZjUE', '2025-03-19 19:10:59.888096'),
('jakopz49t4j4utb4epk5cenms2gp7iya', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttOg5:GqbzkjCZkO5ZjEunoeEoTYC0JFlRcr88UJzPD8AHEqE', '2025-03-15 11:23:37.990714'),
('lv3xkbc9ymzjwbf02uf9ahndfm36vfew', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tsnfo:hphkcqaT2bhayLtEIBF4li3x6zmGlGmKqtpw-8owcRE', '2025-03-13 19:52:52.783146'),
('malq7g98p1odmqmh8ygj9cvj7xutrg0k', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tt4h4:wXDKaUEi1G3knkWVBtAa8caxmxnL1dZ4UwDEE8HSQ2E', '2025-03-14 14:03:18.622721'),
('nmlgsnjkawcfx81hfbure3hxs3cjrv4e', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttAap:-rNereWYNEAkPr6w2wNyRsD0GdxcnissyZlvAEoyZHE', '2025-03-14 20:21:15.177204'),
('nxpua09hquv9sxdhxq8b7h1xlgvg41lp', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvGVP:yzUsMDqA-W9fQVTVaPx-cn7-7rUOKQVxGh6YtJzdic4', '2025-03-20 15:04:19.190033'),
('oxi475cgmnfpldd5scy8eq6vahnhevql', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tsjCJ:wIlwZ_c6OihRfn7PfC_fiS5CJVb3gD0pPHlugftWiiE', '2025-03-13 15:06:07.921247'),
('r6jyk9cxfqkn556fs7ffwm9k97893jw2', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttBtz:NKHNi1xj8SbHeA7jy25mzZkHV8fRA_0MtBXRQ8ORTeI', '2025-03-14 21:45:07.956883'),
('rz7p8edbtu5fv7yi4hyszdbskken3m8i', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1ttqp5:Feq194GxHGDK4hN7LpHKHBCeFcR4Ifq0VUDWXLE6VhY', '2025-03-16 17:26:47.072272'),
('sebgef2917wjfwsatacvajt9zshnh2li', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tsm1O:zFrFTBskAKEBPawPuOlGlfeFhuqGgTvYHppgIqC713g', '2025-03-13 18:07:02.090216'),
('seuxa6f3q9x09iekmm7xq208g198or8n', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tup2H:BwbWt9ldpLP65_whMe-WvjtFSE9Q0MoFqhI3LsM8Kto', '2025-03-19 09:44:25.925146'),
('sv8ade95xqr9c12zbhwtjancakscbgxk', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvkt7:Dl1c83Fp9NshCgnc6lxX7CExT7kqA_ee0jU8m4bJJwY', '2025-03-21 23:30:49.929745'),
('tkmvjrzx17yyormutkm2hkfvtk84lrh5', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvXji:jrRyMPA0VUDRdJ6IuLep0ICgm5UV0QT_LmkSuYJe1xM', '2025-03-21 09:28:14.097996'),
('vmz0qmq08vjxes40egsd7apknqxjtn8j', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvbdG:g_HgquaFPxXLhZuMh3d_5nKOfhRfy_QSKf4H_pPTpgY', '2025-03-21 13:37:50.155111'),
('wtgk3p9uofh3q0fibm9fs4k4vejkvqnt', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tuIfH:KrZcdXDEz4kt9mxQDCfHeI0ZARXuEbuvDqG0FcCJnkw', '2025-03-17 23:10:31.626232'),
('xp2gntljhpxj49zr1yth6ony9jhgpo4s', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tsUhx:IljmN5AOTX4q-wDQL0SDNPmeapUESUVthvK36ZcIJZ0', '2025-03-12 23:37:49.112707'),
('zwhoyt2sc4fymsecgcgxbymlasn66anl', '.eJxVjEsOwjAMBe-SNYpKnLQxS_Y9Q2THDimgVupnhbg7VOoCtm9m3ssk2taatkXnNIi5GDCn340pP3TcgdxpvE02T-M6D2x3xR50sf0k-rwe7t9BpaV-a9RWQXLwJIhNJ9hwYfLhjOSBCghqCJlcCzGyiwgEmRvQ4oLzHYp5fwD3mTgR:1tvFYU:DBwpV-DKkc3BukJGlpnpIQohRKrbZy--IFkhwxArA7s', '2025-03-20 14:03:26.350959');

-- --------------------------------------------------------

--
-- Structure de la table `Observations_causesechec`
--

CREATE TABLE `Observations_causesechec` (
  `id` bigint(20) NOT NULL,
  `description` longtext DEFAULT NULL,
  `fiche_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `Observations_causesechec`
--

INSERT INTO `Observations_causesechec` (`id`, `description`, `fiche_id`) VALUES
(1, 'Aucune cause identifiée', 3),
(2, 'Abandon du nid à cause de prédateurs.', 1),
(3, 'Aucune cause identifiée', 4),
(4, 'Aucune cause identifiée', 5);

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
(1, 'Hirondelle', 'Petit oiseau migrateur', 'https://www.oiseaux.net/oiseaux/hirondelle.html', 1),
(2, 'Mésange', 'Présente dans les jardins', 'https://www.oiseaux.net/oiseaux/mesange.html', 1);

-- --------------------------------------------------------

--
-- Structure de la table `Observations_ficheobservation`
--

CREATE TABLE `Observations_ficheobservation` (
  `num_fiche` int(11) NOT NULL,
  `date_creation` datetime(6) NOT NULL,
  `annee` int(11) NOT NULL,
  `chemin_image` varchar(255) DEFAULT NULL,
  `espece_id` bigint(20) NOT NULL,
  `observateur_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `Observations_ficheobservation`
--

INSERT INTO `Observations_ficheobservation` (`num_fiche`, `date_creation`, `annee`, `chemin_image`, `espece_id`, `observateur_id`) VALUES
(1, '2025-03-07 22:21:29.000000', 2024, 'media/images/fiche1.jpg', 1, 1),
(2, '2025-03-07 22:21:29.000000', 2023, 'media/images/fiche2.png', 2, 2),
(3, '2025-03-08 14:22:12.788440', 2024, NULL, 1, 1),
(4, '2025-03-16 14:30:26.616726', 2025, '', 1, 3),
(5, '2025-03-16 16:30:05.602587', 2025, '', 2, 3);

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
  `categorie` varchar(20) NOT NULL,
  `fiche_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `Observations_historiquevalidation`
--

CREATE TABLE `Observations_historiquevalidation` (
  `id` bigint(20) NOT NULL,
  `ancien_statut` varchar(10) NOT NULL,
  `nouveau_statut` varchar(10) NOT NULL,
  `date_modification` datetime(6) NOT NULL,
  `modifie_par_id` bigint(20) DEFAULT NULL,
  `validation_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `Observations_localisation`
--

CREATE TABLE `Observations_localisation` (
  `id` bigint(20) NOT NULL,
  `commune` varchar(30) NOT NULL,
  `departement` varchar(5) NOT NULL,
  `coordonnees` varchar(30) NOT NULL,
  `latitude` varchar(15) NOT NULL,
  `longitude` varchar(15) NOT NULL,
  `altitude` varchar(10) NOT NULL,
  `paysage` longtext NOT NULL,
  `alentours` longtext NOT NULL,
  `fiche_id` int(11) NOT NULL,
  `lieu_dit` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `Observations_localisation`
--

INSERT INTO `Observations_localisation` (`id`, `commune`, `departement`, `coordonnees`, `latitude`, `longitude`, `altitude`, `paysage`, `alentours`, `fiche_id`, `lieu_dit`) VALUES
(1, 'Bordeaux', '33', '44.8378, -0.5792', '44.837800', '-0.579200', '10m', 'Forêt urbaine', 'Parc naturel proche', 2, 'dit le chêne blanc'),
(2, 'Lyon', '69', '45.7640, 4.8357', '45.764000', '4.835700', '15m', 'Bord de rivière', 'Zone marécageuse', 1, 'vallée de la taupe'),
(3, 'Non spécifiée', '00', '0,0', '0.0', '0.0', '0', 'Non spécifié', 'Non spécifié', 3, 'Roche Torin'),
(4, 'Saint James', '50', '0,0', '', '', '120', 'Campagne normande', 'jardin', 4, 'Poelley'),
(5, 'Saint James', '50', '0,0', '', '', '120', 'Campagne, champs', 'jardin', 5, 'Poelley');

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
  `fiche_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `Observations_nid`
--

INSERT INTO `Observations_nid` (`id`, `nid_prec_t_meme_couple`, `hauteur_nid`, `hauteur_couvert`, `details_nid`, `fiche_id`) VALUES
(1, 0, 0, 0, 'Aucun détail', 3),
(2, 1, 250, 300, 'Situé sur un chêne.', 1),
(3, 1, 220, 350, 'brindille\r\nDuvet', 4),
(4, 1, 150, 200, 'brindille et foin', 5);

-- --------------------------------------------------------

--
-- Structure de la table `Observations_observation`
--

CREATE TABLE `Observations_observation` (
  `id` bigint(20) NOT NULL,
  `date_observation` datetime(6) NOT NULL,
  `nombre_oeufs` int(11) NOT NULL,
  `nombre_poussins` int(11) NOT NULL,
  `observations` longtext DEFAULT NULL,
  `fiche_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `Observations_observation`
--

INSERT INTO `Observations_observation` (`id`, `date_observation`, `nombre_oeufs`, `nombre_poussins`, `observations`, `fiche_id`) VALUES
(1, '2025-03-09 00:19:36.546904', 3, 2, 'Première observation testée.', 1);

-- --------------------------------------------------------

--
-- Structure de la table `Observations_remarque`
--

CREATE TABLE `Observations_remarque` (
  `id` bigint(20) NOT NULL,
  `remarque` varchar(200) NOT NULL,
  `date_remarque` datetime(6) NOT NULL,
  `fiche_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `Observations_remarque`
--

INSERT INTO `Observations_remarque` (`id`, `remarque`, `date_remarque`, `fiche_id`) VALUES
(1, 'Test ajout remarque', '2025-03-09 19:46:05.856697', 1);

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
  `nombre_oeufs_pondus` int(11) NOT NULL,
  `nombre_oeufs_eclos` int(11) NOT NULL,
  `nombre_oeufs_non_eclos` int(11) NOT NULL,
  `nombre_poussins` int(11) NOT NULL,
  `fiche_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `Observations_resumeobservation`
--

INSERT INTO `Observations_resumeobservation` (`id`, `premier_oeuf_pondu_jour`, `premier_oeuf_pondu_mois`, `premier_poussin_eclos_jour`, `premier_poussin_eclos_mois`, `premier_poussin_volant_jour`, `premier_poussin_volant_mois`, `nombre_oeufs_pondus`, `nombre_oeufs_eclos`, `nombre_oeufs_non_eclos`, `nombre_poussins`, `fiche_id`) VALUES
(1, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, 0, 3),
(2, 5, 4, 20, 4, 5, 5, 4, 3, 1, 3, 1),
(3, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, 0, 4),
(4, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, 0, 5);

-- --------------------------------------------------------

--
-- Structure de la table `Observations_utilisateur`
--

CREATE TABLE `Observations_utilisateur` (
  `id` bigint(20) NOT NULL,
  `email` varchar(254) NOT NULL,
  `role` varchar(15) NOT NULL,
  `est_valide` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `last_name` varchar(150) NOT NULL,
  `password` varchar(128) NOT NULL,
  `username` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `Observations_utilisateur`
--

INSERT INTO `Observations_utilisateur` (`id`, `email`, `role`, `est_valide`, `date_joined`, `first_name`, `is_active`, `is_staff`, `is_superuser`, `last_login`, `last_name`, `password`, `username`) VALUES
(1, 'jean.dupont@example.com', 'observateur', 1, '2025-03-12 14:43:38.360118', 'jean', 1, 0, 0, NULL, 'dupont', 'pbkdf2_sha256$216000$dummy_salt$dummy_hash', 'jean.dupont'),
(2, 'sophie.martin@example.com', 'observateur', 1, '2025-03-12 14:43:38.360118', 'sophie', 1, 0, 0, NULL, 'martin', 'pbkdf2_sha256$216000$dummy_salt$dummy_hash', 'sophie.martin'),
(3, 'schneider.jm@free.fr', 'administrateur', 1, '2025-03-12 16:07:54.000000', 'Jean-Marie', 1, 1, 1, '2025-03-21 22:30:49.922858', 'Schneider', 'pbkdf2_sha256$870000$LAst12R1u4nLDrRHjuK72t$MClni+qPnm9Dd2vk7RcSmJyazv63PGU0H8HS68ShHK0=', 'jms'),
(5, 'toto.albi@free.fr', 'observateur', 1, '2025-03-12 17:42:15.000000', 'toto', 1, 0, 0, '2025-03-12 17:42:35.000000', 'albi', 'password', 'toto_25');

-- --------------------------------------------------------

--
-- Structure de la table `Observations_utilisateur_groups`
--

CREATE TABLE `Observations_utilisateur_groups` (
  `id` bigint(20) NOT NULL,
  `utilisateur_id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `Observations_utilisateur_user_permissions`
--

CREATE TABLE `Observations_utilisateur_user_permissions` (
  `id` bigint(20) NOT NULL,
  `utilisateur_id` bigint(20) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `Observations_validation`
--

CREATE TABLE `Observations_validation` (
  `id` bigint(20) NOT NULL,
  `date_modification` datetime(6) NOT NULL,
  `statut` varchar(10) NOT NULL,
  `fiche_id` int(11) NOT NULL,
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
  ADD KEY `django_admin_log_user_id_fk` (`user_id`);

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
  ADD PRIMARY KEY (`num_fiche`),
  ADD KEY `Observations_ficheob_espece_id_f87d4ff5_fk_Observati` (`espece_id`),
  ADD KEY `Observations_ficheob_observateur_id_77755281_fk_Observati` (`observateur_id`);

--
-- Index pour la table `Observations_historiquemodification`
--
ALTER TABLE `Observations_historiquemodification`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Observations_histori_fiche_id_72fff059_fk_Observati` (`fiche_id`),
  ADD KEY `Observations_historiquemodification_categorie_9f5d600c` (`categorie`);

--
-- Index pour la table `Observations_historiquevalidation`
--
ALTER TABLE `Observations_historiquevalidation`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Observations_histori_modifie_par_id_7227ef49_fk_Observati` (`modifie_par_id`),
  ADD KEY `Observations_histori_validation_id_815caeec_fk_Observati` (`validation_id`);

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
-- Index pour la table `Observations_remarque`
--
ALTER TABLE `Observations_remarque`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Observations_remarqu_fiche_id_fe2c590d_fk_Observati` (`fiche_id`);

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
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `username_2` (`username`);

--
-- Index pour la table `Observations_utilisateur_groups`
--
ALTER TABLE `Observations_utilisateur_groups`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `Observations_utilisateur_user_permissions`
--
ALTER TABLE `Observations_utilisateur_user_permissions`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `Observations_validation`
--
ALTER TABLE `Observations_validation`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Observations_validat_fiche_id_5382a7cd_fk_Observati` (`fiche_id`),
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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=73;

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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT pour la table `django_migrations`
--
ALTER TABLE `django_migrations`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=27;

--
-- AUTO_INCREMENT pour la table `Observations_causesechec`
--
ALTER TABLE `Observations_causesechec`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT pour la table `Observations_espece`
--
ALTER TABLE `Observations_espece`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT pour la table `Observations_ficheobservation`
--
ALTER TABLE `Observations_ficheobservation`
  MODIFY `num_fiche` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT pour la table `Observations_historiquemodification`
--
ALTER TABLE `Observations_historiquemodification`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `Observations_historiquevalidation`
--
ALTER TABLE `Observations_historiquevalidation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `Observations_localisation`
--
ALTER TABLE `Observations_localisation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT pour la table `Observations_nid`
--
ALTER TABLE `Observations_nid`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT pour la table `Observations_observation`
--
ALTER TABLE `Observations_observation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `Observations_remarque`
--
ALTER TABLE `Observations_remarque`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `Observations_resumeobservation`
--
ALTER TABLE `Observations_resumeobservation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT pour la table `Observations_utilisateur`
--
ALTER TABLE `Observations_utilisateur`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT pour la table `Observations_utilisateur_groups`
--
ALTER TABLE `Observations_utilisateur_groups`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `Observations_utilisateur_user_permissions`
--
ALTER TABLE `Observations_utilisateur_user_permissions`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

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
  ADD CONSTRAINT `django_admin_log_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `Observations_utilisateur` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `Observations_causesechec`
--
ALTER TABLE `Observations_causesechec`
  ADD CONSTRAINT `Observations_causese_fiche_id_ef17440f_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`num_fiche`);

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
  ADD CONSTRAINT `Observations_histori_fiche_id_72fff059_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`num_fiche`);

--
-- Contraintes pour la table `Observations_historiquevalidation`
--
ALTER TABLE `Observations_historiquevalidation`
  ADD CONSTRAINT `Observations_histori_modifie_par_id_7227ef49_fk_Observati` FOREIGN KEY (`modifie_par_id`) REFERENCES `Observations_utilisateur` (`id`),
  ADD CONSTRAINT `Observations_histori_validation_id_815caeec_fk_Observati` FOREIGN KEY (`validation_id`) REFERENCES `Observations_validation` (`id`);

--
-- Contraintes pour la table `Observations_localisation`
--
ALTER TABLE `Observations_localisation`
  ADD CONSTRAINT `Observations_localis_fiche_id_38dd145c_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`num_fiche`);

--
-- Contraintes pour la table `Observations_nid`
--
ALTER TABLE `Observations_nid`
  ADD CONSTRAINT `Observations_nid_fiche_id_b11b0396_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`num_fiche`);

--
-- Contraintes pour la table `Observations_observation`
--
ALTER TABLE `Observations_observation`
  ADD CONSTRAINT `Observations_observa_fiche_id_ab3214cf_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`num_fiche`);

--
-- Contraintes pour la table `Observations_remarque`
--
ALTER TABLE `Observations_remarque`
  ADD CONSTRAINT `Observations_remarqu_fiche_id_fe2c590d_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`num_fiche`);

--
-- Contraintes pour la table `Observations_resumeobservation`
--
ALTER TABLE `Observations_resumeobservation`
  ADD CONSTRAINT `Observations_resumeo_fiche_id_30e7b36b_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`num_fiche`);

--
-- Contraintes pour la table `Observations_validation`
--
ALTER TABLE `Observations_validation`
  ADD CONSTRAINT `Observations_validat_fiche_id_5382a7cd_fk_Observati` FOREIGN KEY (`fiche_id`) REFERENCES `Observations_ficheobservation` (`num_fiche`),
  ADD CONSTRAINT `Observations_validat_reviewer_id_a2492ad2_fk_Observati` FOREIGN KEY (`reviewer_id`) REFERENCES `Observations_utilisateur` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
