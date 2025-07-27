import { useState, useCallback } from 'react';
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface ImportResult {
  filename: string;
  total_rows: number;
  valid_rows: number;
  validation_errors: any[];
  conflicts: any[];
  success: boolean;
  processing_time_ms: number;
}

export function ScheduleImport() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [previewData, setPreviewData] = useState<any[]>([]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.type === 'text/csv' || droppedFile.name.endsWith('.csv'))) {
      setFile(droppedFile);
      // In real app, parse CSV for preview
      setPreviewData([
        { date: '2024-03-01', time: '09:00', program: 'Yoga Basics', instructor: 'Sarah Johnson', room: 'Studio A' },
        { date: '2024-03-01', time: '10:30', program: 'Advanced Swimming', instructor: 'Mike Chen', room: 'Pool' },
        { date: '2024-03-01', time: '14:00', program: 'Photography Workshop', instructor: 'Emma Davis', room: 'Room 201' },
      ]);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      // In real app, parse CSV for preview
      setPreviewData([
        { date: '2024-03-01', time: '09:00', program: 'Yoga Basics', instructor: 'Sarah Johnson', room: 'Studio A' },
        { date: '2024-03-01', time: '10:30', program: 'Advanced Swimming', instructor: 'Mike Chen', room: 'Pool' },
        { date: '2024-03-01', time: '14:00', program: 'Photography Workshop', instructor: 'Emma Davis', room: 'Room 201' },
      ]);
    }
  }, []);

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);

    // Simulate upload - in real app, this would call the API
    setTimeout(() => {
      setImportResult({
        filename: file.name,
        total_rows: 15,
        valid_rows: 14,
        validation_errors: [
          { row_number: 7, field: 'time', message: 'Invalid time format' }
        ],
        conflicts: [],
        success: true,
        processing_time_ms: 234
      });
      setIsUploading(false);
    }, 2000);
  };

  const resetUpload = () => {
    setFile(null);
    setImportResult(null);
    setPreviewData([]);
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Schedule Import</h1>
        <p className="mt-1 text-sm text-gray-600">
          Import program schedules from CSV files to automatically create events in the system.
        </p>
      </div>

      {!importResult ? (
        <>
          {/* Upload area */}
          <Card>
            <CardHeader>
              <CardTitle>Upload Schedule File</CardTitle>
              <CardDescription>
                Upload a CSV file containing your program schedule. The file should include columns for date, time, program name, instructor, and room.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                  "relative rounded-lg border-2 border-dashed p-12 text-center transition-colors",
                  isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300",
                  file && "bg-gray-50"
                )}
              >
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={isUploading}
                />

                {file ? (
                  <div className="space-y-2">
                    <FileSpreadsheet className="mx-auto h-12 w-12 text-green-600" />
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="text-sm text-gray-600">
                      Drop your CSV file here, or click to select
                    </p>
                    <p className="text-xs text-gray-500">
                      Maximum file size: 10MB
                    </p>
                  </div>
                )}
              </div>

              {file && (
                <div className="mt-4 flex justify-end gap-2">
                  <Button variant="outline" onClick={resetUpload} disabled={isUploading}>
                    Cancel
                  </Button>
                  <Button onClick={handleUpload} disabled={isUploading}>
                    {isUploading ? 'Uploading...' : 'Import Schedule'}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Preview */}
          {file && previewData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Preview</CardTitle>
                <CardDescription>
                  First few rows from your CSV file
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Date</th>
                        <th className="text-left p-2">Time</th>
                        <th className="text-left p-2">Program</th>
                        <th className="text-left p-2">Instructor</th>
                        <th className="text-left p-2">Room</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.map((row, i) => (
                        <tr key={i} className="border-b">
                          <td className="p-2">{row.date}</td>
                          <td className="p-2">{row.time}</td>
                          <td className="p-2">{row.program}</td>
                          <td className="p-2">{row.instructor}</td>
                          <td className="p-2">{row.room}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        /* Results */
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Import Results</CardTitle>
                <CardDescription>
                  Processed in {importResult.processing_time_ms}ms
                </CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={resetUpload}>
                <X className="h-4 w-4 mr-1" />
                New Import
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className={cn(
              "flex items-center gap-3 p-4 rounded-lg",
              importResult.success ? "bg-green-50" : "bg-red-50"
            )}>
              {importResult.success ? (
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600" />
              )}
              <div>
                <p className={cn(
                  "font-medium",
                  importResult.success ? "text-green-900" : "text-red-900"
                )}>
                  {importResult.success ? 'Import Successful' : 'Import Failed'}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {importResult.valid_rows} of {importResult.total_rows} rows imported successfully
                </p>
              </div>
            </div>

            {importResult.validation_errors.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Validation Errors</h4>
                <div className="space-y-1">
                  {importResult.validation_errors.map((error, i) => (
                    <div key={i} className="text-sm text-red-600">
                      Row {error.row_number}: {error.message}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
