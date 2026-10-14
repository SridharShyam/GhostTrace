import {
  Component,
  OnInit,
  signal,
  computed,
  ElementRef,
  ViewChild,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

// Angular Material Components
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatChipsModule } from '@angular/material/chips';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatBadgeModule } from '@angular/material/badge';
import { MatDividerModule } from '@angular/material/divider';

import { GhostTraceService, AuditResponse } from './ghosttrace.service';

interface ReviewItem {
  id: number;
  word: string;
  alternatives: string[];
  selectedAlternative: string;
  accepted: boolean;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatButtonToggleModule,
    MatChipsModule,
    MatCheckboxModule,
    MatSelectModule,
    MatFormFieldModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatSnackBarModule,
    MatBadgeModule,
    MatDividerModule
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  private service = inject(GhostTraceService);
  private sanitizer = inject(DomSanitizer);
  private snackBar = inject(MatSnackBar);

  @ViewChild('editorRef') editorRef!: ElementRef<HTMLTextAreaElement>;
  @ViewChild('heatmapRef') heatmapRef!: ElementRef<HTMLDivElement>;
  @ViewChild('fileInputRef') fileInputRef!: ElementRef<HTMLInputElement>;

  // Reactive state signals
  mode = signal<'general' | 'academic'>('general');
  rawText = signal<string>(
    'In this study, we delve into a revolutionary approach that provides seamless optimization for next-level performance.'
  );
  auditData = signal<AuditResponse | null>(null);
  isLoading = signal<boolean>(false);
  reviewQueue = signal<ReviewItem[]>([]);

  // Computed state metrics
  score = computed(() => this.auditData()?.score ?? 5);
  wordCount = computed(() => this.auditData()?.word_count ?? 0);
  burstiness = computed(() => this.auditData()?.burstiness?.std_dev ?? 0);
  isMonotonous = computed(() => this.auditData()?.burstiness?.is_monotonous ?? false);

  watermarkCount = computed(() => {
    const wm = this.auditData()?.watermarks;
    if (!wm) return 0;
    return Object.values(wm).reduce((a, b) => a + b, 0);
  });

  density = computed(() => {
    const data = this.auditData();
    if (!data || !data.word_count) return 0;
    const vocabCount = data.hits?.vocab?.length ?? 0;
    const phraseCount = data.hits?.phrases?.length ?? 0;
    return Number(((vocabCount + phraseCount) / data.word_count * 100).toFixed(1));
  });

  safeHeatmapHtml = computed<SafeHtml>(() => {
    const text = this.rawText();
    const data = this.auditData();
    if (!text.trim() || !data) {
      return this.sanitizer.bypassSecurityTrustHtml('');
    }

    let escaped = this.escapeHtml(text);

    // Red highlights for vocab slop
    if (data.hits?.vocab) {
      for (const [w] of data.hits.vocab) {
        const re = new RegExp(`\\b(${this.escapeRegex(w)}[a-z]*)\\b`, 'gi');
        escaped = escaped.replace(re, '<mark class="slop-tell">$1</mark>');
      }
    }

    // Yellow highlights for academic hype / buzzwords
    if (data.hits?.academic_hype) {
      for (const [w] of data.hits.academic_hype) {
        const re = new RegExp(`\\b(${this.escapeRegex(w)})\\b`, 'gi');
        escaped = escaped.replace(re, '<mark class="slop-hype">$1</mark>');
      }
    }

    return this.sanitizer.bypassSecurityTrustHtml(escaped);
  });

  private debounceTimer?: any;

  ngOnInit() {
    this.runAudit();
  }

  onModeChange(newMode: 'general' | 'academic') {
    this.mode.set(newMode);
    this.runAudit();
  }

  onTextChange(text: string) {
    this.rawText.set(text);
    this.syncScroll();
    clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      this.runAudit();
    }, 250);
  }

  syncScroll() {
    if (this.editorRef && this.heatmapRef) {
      this.heatmapRef.nativeElement.scrollTop = this.editorRef.nativeElement.scrollTop;
      this.heatmapRef.nativeElement.scrollLeft = this.editorRef.nativeElement.scrollLeft;
    }
  }

  triggerFileUpload() {
    this.fileInputRef?.nativeElement.click();
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    this.isLoading.set(true);
    this.service.uploadDocument(file).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        if (res.text) {
          this.rawText.set(res.text);
          if (file.name.endsWith('.tex')) {
            this.mode.set('academic');
          }
          this.runAudit();
          this.showSnack(`Document "${file.name}" loaded successfully.`);
        }
      },
      error: (err) => {
        this.isLoading.set(false);
        this.showSnack(`Failed to extract text: ${err.message || 'Network error'}`);
      }
    });
  }

  runAudit() {
    const text = this.rawText();
    if (!text.trim()) {
      this.auditData.set(null);
      this.reviewQueue.set([]);
      return;
    }

    this.service.auditText(text, this.mode()).subscribe({
      next: (res) => {
        this.auditData.set(res);
        this.populateReviewQueue(res.suggestions);
      },
      error: (err) => {
        console.error('Audit failed:', err);
      }
    });
  }

  populateReviewQueue(suggestions: Record<string, string[]>) {
    if (!suggestions) {
      this.reviewQueue.set([]);
      return;
    }

    const items: ReviewItem[] = Object.entries(suggestions).map(([word, alts], idx) => ({
      id: idx,
      word,
      alternatives: alts,
      selectedAlternative: alts[0] || '',
      accepted: true
    }));

    this.reviewQueue.set(items);
  }

  // One-Click Confirmed Humanize
  applyConfirmedHumanize() {
    const queue = this.reviewQueue();
    let updated = this.rawText();
    let count = 0;

    for (const item of queue) {
      if (item.accepted && item.selectedAlternative) {
        const re = new RegExp(`\\b${this.escapeRegex(item.word)}\\b`, 'gi');
        updated = updated.replace(re, (match) => {
          if (match === match.toUpperCase()) return item.selectedAlternative.toUpperCase();
          if (match[0] === match[0].toUpperCase()) {
            return item.selectedAlternative.charAt(0).toUpperCase() + item.selectedAlternative.slice(1);
          }
          return item.selectedAlternative;
        });
        count++;
      }
    }

    // Purge intrinsic watermarks & zero-width anomalies
    updated = this.purgeWatermarks(updated);

    this.rawText.set(updated);
    this.runAudit();
    this.showSnack(`✨ Humanized ${count} word(s) and sanitized intrinsic AI watermarks!`);
  }

  copySanitizedText() {
    const clean = this.purgeWatermarks(this.rawText());
    navigator.clipboard.writeText(clean).then(() => {
      this.showSnack('📋 Sanitized text copied to clipboard!');
    });
  }

  downloadSanitizedText() {
    const clean = this.purgeWatermarks(this.rawText());
    const blob = new Blob([clean], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ghosttrace_sanitized.txt';
    a.click();
    URL.revokeObjectURL(url);
    this.showSnack('📥 Downloaded sanitized file.');
  }

  private purgeWatermarks(str: string): string {
    return str
      .replace(/[\u200B\u200C\u200D\uFEFF\u200E\u200F\u00AD]/g, '')
      .replace(/[\u00A0\u2000-\u200A\u202F\u205F\u3000]/g, ' ')
      .replace(/‑/g, '-');
  }

  private escapeHtml(text: string): string {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  }

  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  private showSnack(msg: string) {
    this.snackBar.open(msg, 'Close', {
      duration: 3500,
      horizontalPosition: 'end',
      verticalPosition: 'bottom',
      panelClass: ['gt-snackbar']
    });
  }
}
