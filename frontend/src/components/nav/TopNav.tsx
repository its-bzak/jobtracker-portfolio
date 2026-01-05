import { NavLink } from "react-router-dom";
import styles from "./TopNav.module.css";

export default function TopNav() {
  return (
    <nav className={styles.nav}>
      <div className={styles.left}>

        <NavLink
          to="/jobs"
          className={({ isActive }) =>
            isActive ? styles.activeLink : styles.link
          }
        >
          Jobs
        </NavLink>

        <NavLink
          to="/applications"
          className={({ isActive }) =>
            isActive ? styles.activeLink : styles.link
          }
        >
          My Applications
        </NavLink>

        <NavLink
          to="/messages"
          className={({ isActive }) =>
            isActive ? styles.activeLink : styles.link
          }
        >
          Messages
        </NavLink>

        <NavLink
          to="/profile"
          className={({ isActive }) =>
            isActive ? styles.activeLink : styles.link
          }
        >
          Profile
        </NavLink>
      </div>

      <div className={styles.right}>
        <NavLink to="/logout" className={styles.logout}>
          Logout
        </NavLink>
      </div>
    </nav>
  );
}
