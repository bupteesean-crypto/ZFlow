import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";

// Import pages
import LandingPage from "../pages/landing/index.vue";
import LoginPage from "../pages/login/index.vue";
import MaterialsPage from "../pages/materials/index.vue";
import EditorPage from "../pages/editor/index.vue";
import AssetsPage from "../pages/assets/index.vue";
import SpacePage from "../pages/space/index.vue";
import AdminUsersPage from "../pages/admin-users/index.vue";
import ApiSettingsPage from "../pages/api-settings/index.vue";

// Legacy pages (kept for compatibility)
import DashboardPage from "../pages/dashboard/index.vue";
import TasksPage from "../pages/tasks/list.vue";
import TaskDetailPage from "../pages/tasks/detail.vue";

const routes: RouteRecordRaw[] = [
  // ZFlow pages
  {
    path: "/",
    name: "landing",
    component: LandingPage,
    meta: { layout: "app-shell" },
  },
  {
    path: "/login",
    name: "login",
    component: LoginPage,
    meta: { layout: "bare" },
  },
  {
    path: "/materials",
    name: "materials",
    component: MaterialsPage,
    meta: { layout: "app-shell" },
  },
  {
    path: "/editor",
    name: "editor",
    component: EditorPage,
    meta: { layout: "app-shell" },
  },
  {
    path: "/assets",
    name: "assets",
    component: AssetsPage,
    meta: { layout: "app-shell" },
  },
  {
    path: "/space",
    name: "space",
    component: SpacePage,
    meta: { layout: "app-shell" },
  },
  {
    path: "/admin/users",
    name: "admin-users",
    component: AdminUsersPage,
    meta: { layout: "bare" },
  },
  {
    path: "/settings/api",
    name: "api-settings",
    component: ApiSettingsPage,
    meta: { layout: "app-shell" },
  },

  // Legacy ZFlow pages (kept for compatibility)
  {
    path: "/dashboard",
    name: "dashboard",
    component: DashboardPage,
    meta: { layout: "legacy" },
  },
  {
    path: "/tasks",
    name: "tasks",
    component: TasksPage,
    meta: { layout: "legacy" },
  },
  {
    path: "/tasks/:id",
    name: "task-detail",
    component: TaskDetailPage,
    meta: { layout: "legacy" },
  },

  // 404 fallback
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    redirect: "/",
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Navigation guard for authentication
router.beforeEach((to, _from, next) => {
  const isAuthenticated =
    sessionStorage.getItem('authenticated') === 'true' ||
    Boolean(sessionStorage.getItem('session_token'));
  let isPlatformAdmin = false;
  const rawUser = sessionStorage.getItem('user');
  if (rawUser) {
    try {
      const parsed = JSON.parse(rawUser);
      isPlatformAdmin = Boolean(parsed?.is_platform_admin);
    } catch {
      isPlatformAdmin = false;
    }
  }

  // Allow access to login and admin user management pages
  if (to.name === 'login') {
    next();
    return;
  }
  if (to.name === 'admin-users') {
    if (!isAuthenticated) {
      next({ name: 'login', query: { redirect: to.fullPath } });
      return;
    }
    if (!isPlatformAdmin) {
      next({ name: 'landing' });
      return;
    }
    next();
    return;
  }

  if (to.name === 'api-settings') {
    if (!isAuthenticated) {
      next({ name: 'login', query: { redirect: to.fullPath } });
      return;
    }
    next();
    return;
  }

  // Require authentication for protected routes
  const protectedRoutes = ['landing', 'materials', 'editor', 'assets', 'space'];
  if (protectedRoutes.includes(to.name as string) && !isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } });
  } else {
    next();
  }
});

export default router;
