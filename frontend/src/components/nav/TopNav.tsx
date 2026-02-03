import { NavLink } from "react-router-dom";
import styles from "./TopNav.module.css";
import { useAuth } from "../../auth/AuthContext";

type NavItem = { to: string; label: string };

/* Nav items for different account types */

// Applicant nav items
const applicantItems: NavItem[] = [
  { to: "/applicant/jobs", label: "Jobs" },
  { to: "/applicant/applications", label: "My Applications" },
];
// Employer nav items
const employerItems: NavItem[] = [
  { to: "/employer/jobs", label: "Job Postings" },
  { to: "/employer/applications", label: "Candidates" },
];

export default function TopNav() {
  const { accountType, loading, hasNewApplicationDraft } = useAuth();

  const items =
    accountType === "EM" ? employerItems : applicantItems;

  return (
    <nav className={styles.nav}>
      <div className={styles.left}>
        <span className={styles.logo}>JobTracker</span>

        {!loading &&
          items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? styles.activeLink : styles.link
              }
            >
              <span>{item.label}</span>
              {item.to === '/applicant/applications' && hasNewApplicationDraft && (
                <span className={styles.dot} aria-hidden />
              )}
            </NavLink>
          ))}
      </div>

      <div className={styles.right}>
        <NavLink to="/logout" className={styles.logout}>
          Logout
        </NavLink>
      </div>
    </nav>
  );
}
