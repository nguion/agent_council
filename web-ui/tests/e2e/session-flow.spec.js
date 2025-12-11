/**
 * End-to-End tests for Agent Council web interface using Playwright.
 * 
 * Tests cover:
 * - Complete session flow (create → build → edit → execute → review)
 * - Error handling and retry mechanisms
 * - Navigation between steps
 * - Session persistence and resume
 * - Database busy error recovery
 * 
 * Setup:
 *   npm install -D @playwright/test
 *   npx playwright install
 * 
 * Run:
 *   npx playwright test
 */

const { test, expect } = require('@playwright/test');

// Test configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const APP_BASE_URL = process.env.APP_BASE_URL || 'http://localhost:5173';

test.describe('Session Flow - Happy Path', () => {
  let sessionId;

  test('should create a new session with question', async ({ page }) => {
    await page.goto(APP_BASE_URL);
    
    // Enter question
    await page.fill('textarea', 'What is the best way to test an Agent Council system?');
    
    // Click Build Council
    await page.click('button:has-text("Build Council")');
    
    // Should navigate to build page
    await expect(page).toHaveURL(/\/sessions\/.*\/build/);
    
    // Extract session ID from URL
    const url = page.url();
    sessionId = url.match(/sessions\/(session_\d+_\w+)/)[1];
    
    console.log('Created session:', sessionId);
  });

  test('should build council configuration', async ({ page }) => {
    await page.goto(APP_BASE_URL);
    
    // Wait for council to build
    await page.waitForSelector('text=agents proposed', { timeout: 60000 });
    
    // Should show agent cards
    const agentCount = await page.locator('[class*="agent"]').count();
    expect(agentCount).toBeGreaterThan(0);
  });

  test('should navigate to edit step', async ({ page }) => {
    // Navigate to a session build page first
    await page.goto(`${APP_BASE_URL}/sessions/${sessionId}/build`);
    
    // Click Review & Edit
    await page.click('button:has-text("Review & Edit Council")');
    
    // Should navigate to edit page
    await expect(page).toHaveURL(/\/sessions\/.*\/edit/);
  });

  test('should save edits and navigate to execute', async ({ page }) => {
    await page.goto(`${APP_BASE_URL}/sessions/${sessionId}/edit`);
    
    // Edit first agent name
    const firstAgentName = await page.locator('input[type="text"]').first();
    await firstAgentName.fill('Modified Test Agent');
    
    // Click Save & Execute
    await page.click('button:has-text("Save & Execute")');
    
    // Should navigate to execute page
    await expect(page).toHaveURL(/\/sessions\/.*\/execute/);
  });

  test('should execute council (mocked)', async ({ page, context }) => {
    // Mock the execute endpoint to avoid actual LLM calls
    await context.route(`${API_BASE_URL}/api/sessions/*/execute`, route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'accepted', message: 'Execution started' })
      });
    });
    
    await page.goto(`${APP_BASE_URL}/sessions/${sessionId}/execute`);
    
    // Click Start Execution
    await page.click('button:has-text("Start Execution")');
    
    // Should show executing state
    await expect(page.locator('text=in Progress')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Error Handling', () => {
  test('should display error when build fails', async ({ page, context }) => {
    await page.goto(APP_BASE_URL);
    
    // Enter question
    await page.fill('textarea', 'Test question for error scenario');
    
    // Mock build_council to return error
    await context.route(`${API_BASE_URL}/api/sessions/*/build_council`, route => {
      route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ 
          detail: 'Database is temporarily busy, please retry in a few seconds.' 
        })
      });
    });
    
    await page.click('button:has-text("Build Council")');
    
    // Should show error message
    await expect(page.locator('text=Database is temporarily busy')).toBeVisible();
    
    // Should have retry button
    await expect(page.locator('button:has-text("Try Again")')).toBeVisible();
  });

  test('should display error when execution fails precondition', async ({ page, context }) => {
    // Create session without council config
    const response = await context.request.post(`${API_BASE_URL}/api/sessions`, {
      data: { question: 'Test without council' }
    });
    const { session_id } = await response.json();
    
    // Navigate directly to execute
    await page.goto(`${APP_BASE_URL}/sessions/${session_id}/execute`);
    
    // Try to execute
    await page.click('button:has-text("Start Execution")');
    
    // Should show precondition error
    await expect(page.locator('text=/council.*required/i')).toBeVisible();
  });

  test('should handle navigation errors gracefully', async ({ page }) => {
    // Navigate to non-existent session
    await page.goto(`${APP_BASE_URL}/sessions/nonexistent_session/build`);
    
    // Should show 404 or redirect to sessions list
    await expect(page.locator('text=/not found|no sessions/i')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Session Persistence', () => {
  test('should persist session across page refreshes', async ({ page }) => {
    await page.goto(APP_BASE_URL);
    
    // Create session
    await page.fill('textarea', 'Persistence test question');
    await page.click('button:has-text("Build Council")');
    
    // Wait for build page
    await page.waitForURL(/\/sessions\/.*\/build/);
    const url1 = page.url();
    
    // Refresh page
    await page.reload();
    
    // Should stay on same session
    const url2 = page.url();
    expect(url1).toBe(url2);
    
    // Question should be preserved
    await expect(page.locator('text=Persistence test question')).toBeVisible();
  });

  test('should list sessions on sessions page', async ({ page }) => {
    await page.goto(`${APP_BASE_URL}/sessions`);
    
    // Should show sessions list
    await expect(page.locator('text=Agent Council Sessions')).toBeVisible();
    
    // Should have New Session button
    await expect(page.locator('button:has-text("New Session")')).toBeVisible();
  });
});

test.describe('Navigation', () => {
  test('should navigate between steps using Back button', async ({ page, context }) => {
    // Create and build session
    const response = await context.request.post(`${API_BASE_URL}/api/sessions`, {
      data: { question: 'Navigation test' }
    });
    const { session_id } = await response.json();
    
    // Go to execute page
    await page.goto(`${APP_BASE_URL}/sessions/${session_id}/execute`);
    
    // Click Back to Edit
    await page.click('button:has-text("Back")');
    
    // Should navigate to previous step
    await expect(page).toHaveURL(/\/(edit|build)$/);
  });

  test('should navigate using sidebar session list', async ({ page }) => {
    await page.goto(APP_BASE_URL);
    
    // Sidebar should be visible
    await expect(page.locator('text=My Sessions')).toBeVisible();
    
    // Click View All Sessions
    await page.click('button:has-text("View All Sessions")');
    
    // Should navigate to sessions list
    await expect(page).toHaveURL(/\/sessions$/);
  });
});

test.describe('Loading States', () => {
  test('should show loading state during build', async ({ page, context }) => {
    await page.goto(APP_BASE_URL);
    
    await page.fill('textarea', 'Loading state test');
    
    // Delay build_council response
    await context.route(`${API_BASE_URL}/api/sessions/*/build_council`, route => {
      setTimeout(() => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ agents: [] })
        });
      }, 2000);
    });
    
    await page.click('button:has-text("Build Council")');
    
    // Should show loading state
    await expect(page.locator('text=Creating Session')).toBeVisible();
  });

  test('should disable buttons during save operations', async ({ page, context }) => {
    const response = await context.request.post(`${API_BASE_URL}/api/sessions`, {
      data: { question: 'Button disable test' }
    });
    const { session_id } = await response.json();
    
    await page.goto(`${APP_BASE_URL}/sessions/${session_id}/edit`);
    
    // Click save button
    const saveButton = page.locator('button:has-text("Save")');
    await saveButton.click();
    
    // Button should be disabled during save
    await expect(saveButton).toBeDisabled();
  });
});

