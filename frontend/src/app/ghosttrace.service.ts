import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AuditHits {
  vocab?: Array<[string, number]>;
  phrases?: Array<[string, number, string[]?] | any>;
  academic_hype?: Array<[string, number]>;
  intro_cliches?: Array<[string, number]>;
  chatgpt_isms?: Array<[string, number]>;
  ai_connectors?: Array<[string, number]>;
  [key: string]: any;
}

export interface BurstinessInfo {
  std_dev: number;
  avg_len?: number;
  mean_length?: number;
  is_monotonous: boolean;
  sentence_lengths: number[];
  entropy?: number;
  passive_ratio?: number;
  min_len?: number;
  max_len?: number;
}

export interface AuditResponse {
  mode: string;
  word_count: number;
  score: number;
  hits: AuditHits;
  burstiness: BurstinessInfo;
  watermarks: Record<string, number>;
  suggestions: Record<string, string[]>;
}

export interface UploadResponse {
  filename: string;
  text: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class GhostTraceService {
  private http = inject(HttpClient);
  // Uses relative path when hosted on same port or proxy
  private baseUrl = '';

  auditText(text: string, mode: string = 'general'): Observable<AuditResponse> {
    return this.http.post<AuditResponse>(`${this.baseUrl}/api/audit`, { text, mode });
  }

  uploadDocument(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadResponse>(`${this.baseUrl}/api/upload`, formData);
  }
}
