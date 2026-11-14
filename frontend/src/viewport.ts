/**
 * Viewport Cinema Canvas Renderer (TypeScript)
 * Handles smooth curtain transitions, pan & zoom constraints, and fullscreen API.
 */
export class ViewportManager {
  private boundsElement: HTMLElement | null;
  private curtainDivider: HTMLElement | null;
  private isDraggingCurtain: boolean = false;

  constructor() {
    this.boundsElement = document.getElementById('canvasBounds');
    this.curtainDivider = document.getElementById('curtainDivider');
    this.initEvents();
  }

  private initEvents(): void {
    if (!this.curtainDivider) return;

    this.curtainDivider.addEventListener('mousedown', () => {
      this.isDraggingCurtain = true;
    });

    window.addEventListener('mouseup', () => {
      this.isDraggingCurtain = false;
    });

    window.addEventListener('mousemove', (e: MouseEvent) => {
      if (!this.isDraggingCurtain || !this.boundsElement) return;
      const rect = this.boundsElement.getBoundingClientRect();
      if (rect.width <= 0) return;
      const x = e.clientX - rect.left;
      const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
      this.setCurtain(pct);
    });
  }

  public setCurtain(pct: number): void {
    if (this.curtainDivider) this.curtainDivider.style.left = `${pct}%`;
    const afterClip = document.getElementById('afterClip');
    if (afterClip) afterClip.style.clipPath = `inset(0 0 0 ${pct}%)`;
  }
}
