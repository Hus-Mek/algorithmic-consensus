/** All Arabic UI strings. Single source of truth for the interface. */

const ar = {
  // App
  appName: 'الوفاق الخوارزمي',
  appSubtitle: 'إطار تداولي لبناء التوافق المجتمعي',

  // Nav
  navParticipant: 'مشارك',
  navDashboard: 'لوحة التحليل',

  // Participant Home
  welcomeTitle: 'مرحباً بك في منصة التوافق',
  welcomeDesc: 'شاركنا رأيك بشكل مجهول وآمن. صوتك يساهم في بناء مستقبل أفضل.',
  joinButton: 'انضم الآن',
  joinedAs: 'معرّفك المجهول',
  goToSubmit: 'أضف رأياً',
  goToVote: 'صوّت على الآراء',
  goToProgress: 'تقدّمي',

  // Status
  statusParticipants: 'مشاركون',
  statusStatements: 'آراء',
  statusVotes: 'أصوات',
  statusCoverage: 'تغطية التصويت',

  // Submit Statement
  submitTitle: 'أضف رأيك',
  submitDesc: 'اكتب فكرتك في 140 حرفاً أو سجّل رسالة صوتية',
  submitTextPlaceholder: 'اكتب رأيك هنا...',
  submitButton: 'إرسال',
  submitAudioButton: 'تسجيل صوتي',
  charsRemaining: 'حرف متبقي',
  sentimentLabel: 'المشاعر المكتشفة',
  submitSuccess: 'تم إرسال رأيك بنجاح',

  // Audio Recorder
  startRecording: 'ابدأ التسجيل',
  stopRecording: 'أوقف التسجيل',
  recording: 'جاري التسجيل...',
  sendRecording: 'إرسال التسجيل',
  discardRecording: 'حذف',

  // Voting
  voteTitle: 'صوّت على الآراء',
  voteDesc: 'اقرأ كل رأي واختر موقفك',
  voteAgree: 'موافق',
  voteDisagree: 'غير موافق',
  votePass: 'تمرير',
  voteComplete: 'أحسنت! صوّتتَ على جميع الآراء المتاحة',
  voteCompleteDesc: 'عُد لاحقاً لرؤية آراء جديدة',

  // Progress
  progressTitle: 'تقدّمي',
  progressVotedOn: 'صوّتتَ على',
  progressOf: 'من',
  progressStatements: 'آراء',
  agreed: 'موافق',
  disagreed: 'غير موافق',
  passed: 'ممرّر',

  // Dashboard
  dashboardTitle: 'لوحة التحليل',
  runAnalysis: 'تشغيل التحليل',
  analysisRunning: 'جاري التحليل...',
  noAnalysis: 'لا توجد نتائج تحليل بعد',
  noAnalysisDesc: 'اضغط "تشغيل التحليل" لمعالجة البيانات',

  // Metrics
  unityScore: 'مؤشر الوحدة',
  consensusIndex: 'مؤشر التوافق',
  clusterCount: 'مجموعات الرأي',
  voteCoverage: 'تغطية التصويت',
  pcaVariance: 'التباين المُفسَّر',
  silhouetteScore: 'فصل المجموعات',

  // Unity Score interpretations
  unityDeep: 'استقطاب حاد. أرضية مشتركة شبه معدومة.',
  unitySome: 'بعض الجسور موجودة. بداية إيجاد أرضية مشتركة.',
  unityStrong: 'توافق قوي يتشكّل. أساس جيد للسياسات.',
  unityHigh: 'اتفاق مرتفع جداً. تحقّق من تنوّع المشاركين.',

  // Charts
  clusterChart: 'خريطة مجموعات الرأي',
  fearHeatmap: 'خريطة المخاوف الجغرافية',
  bridgeStatements: 'الجمل الجسرية',
  bridgeDesc: 'أفكار حصلت على توافق عابر للمجموعات (>60%)',
  bridgeScore: 'درجة الجسر',
  agreementIn: 'التوافق في',

  // Clusters
  clusterSummary: 'ملخص المجموعات',
  participants: 'مشاركون',

  // Toasts
  joinSuccess: 'تم الانضمام بنجاح',
  analysisSuccess: 'اكتمل التحليل',
  analysisError: 'فشل تشغيل التحليل',

  // Empty states
  noVotesYet: 'لم تصوّت على أي رأي بعد',
  noVotesYetDesc: 'ابدأ بالتصويت على الآراء المتاحة',

  // General
  loading: 'جاري التحميل...',
  error: 'حدث خطأ',
  retry: 'إعادة المحاولة',
  back: 'رجوع',
} as const;

export default ar;
