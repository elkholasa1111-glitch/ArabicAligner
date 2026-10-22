# ArabicAligner

**حوّل النص العربي وتسجيله إلى ملف ترجمة SRT قابل للتحرير.**

[English](README.md) · [التنزيل](#التنزيل) · [التجربة السريعة](#التجربة-السريعة) · [دليل الاستخدام](docs/USAGE.md) · [المساعدة](SUPPORT.md)

[![فحوص المصدر](https://github.com/elkholasa1111-glitch/ArabicAligner/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/elkholasa1111-glitch/ArabicAligner/actions/workflows/ci.yml)

يزامن ArabicAligner نصًا عربيًا موجودًا مع تسجيله. يستخدم التعرف المحلي على الكلام لتقدير التوقيت، بينما يأخذ كلمات الترجمة وتشكيلها من النص الذي تقدمه. يتوفر بواجهة سطح مكتب وسطر أوامر على Windows x64 وmacOS بمعالج Intel.

- **احتفظ بنصك:** تُحفظ الكلمات والتشكيل من النص الأصلي، مع توحيد المسافات.
- **اعمل محليًا:** تتضمن حزم الإصدار النماذج ومكونات الصوت؛ المعالجة لا تحتاج حسابًا أو مفتاح API أو اتصالًا بالإنترنت.
- **راجع النتيجة في أدواتك:** اضبط طول مقاطع الترجمة ومدتها، واحفظ SRT بترميز UTF-8 لفتحه في محرر الترجمة أو المونتاج.

## التنزيل

الإصدار الحالي: **[1.2.0-beta.1 — إصدار تجريبي عام](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/tag/v1.2.0-beta.1)**. اختر المثبت المناسب؛ ملفات Source code في GitHub مخصصة للتطوير.

| النظام | التنزيل | النماذج المضمنة |
| --- | --- | --- |
| Windows x64 | [مثبت Windows · نحو 1.93 جيجابايت](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/download/v1.2.0-beta.1/ArabicAligner_1.2.0-beta.1_Windows_x64_Setup.exe) | small السريع وlarge-v3-turbo |
| macOS 15 فأحدث · Intel x86_64 | [ملف DMG للماك · نحو 577 ميجابايت](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/download/v1.2.0-beta.1/ArabicAligner_1.2.0-beta.1_macOS_Intel.dmg) | small السريع |

مثبت Windows غير موقّع بشهادة. تطبيق الماك بتوقيع محلي ad-hoc، ولم يحصل على notarization من Apple. راجع [التثبيت والاستخدام](docs/USAGE.md) و[رسائل النظام](docs/TROUBLESHOOTING.md). ملفات SHA-256 ومصادر المكونات الخارجية مرفقة مع [الإصدار](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/tag/v1.2.0-beta.1).

هدف بناء Windows هو Windows 10/11 x64؛ اختُبرت النسخة المثبتة على Windows Server 2022 x64. حزمة الماك تستهدف macOS 15 فأحدث واختُبرت على macOS 15.7.9 بمعالج Intel. لم نتحقق من Apple Silicon أو Windows ARM أو Linux. الأداء على الأجهزة القديمة، ومنها MacBook Air 2015، يحتاج تجربة على الجهاز نفسه. التفاصيل في [سجل الاختبارات](docs/VERIFICATION.md).

## التجربة السريعة

1. ثبّت حزمة نظامك. على Windows شغّل المثبت لحسابك. على الماك افتح DMG وانسخ **ArabicAligner Preview.app** إلى Applications.
2. [حمّل العينات الأصلية وفك ضغطها](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/download/v1.2.0-beta.1/ArabicAligner_Examples_1.2.0-beta.1.zip). اختر `examples/msa.wav` داخل التطبيق، ثم افتح `examples/msa.txt` بزر **Load TXT**.
3. اختر **small** واضغط **Align Create SRT**. تُحفظ النتيجة بجانب الصوت؛ استخدم **Open SRT** أو **Open Folder** أو **Save As** لفتحها أو نسخها.
4. افتح SRT في محرر ترجمة أو برنامج مونتاج، وراجع التوقيت بالسماع قبل النشر.

عند استخدام تسجيلك، قدّم النص المنطوق فعلًا. يشرح [دليل الاستخدام](docs/USAGE.md) الصيغ والنماذج وأوامر CLI واستعادة العمل بعد الخطأ.

## التطبيق أثناء العمل

لقطات فعلية من النسختين المثبتتين بعد معالجة العينة المتاحة لإعادة الاستخدام، وتشغيل النموذج وحفظ SRT.

| Windows x64 | macOS Intel |
| --- | --- |
| [![تطبيق Windows بعد محاذاة المثال العربي](docs/screenshots/windows-small-msa.png)](docs/screenshots/windows-small-msa.png) | [![تطبيق الماك بعد محاذاة المثال العربي](docs/screenshots/macos-small-msa.png)](docs/screenshots/macos-small-msa.png) |

يمكنك فحص [SRT الناتج على Windows](docs/demo/windows-small-msa.srt) أو [الناتج على الماك](docs/demo/macos-small-msa.srt)، ومقارنتهما مع [النص والصوت الأصليين](examples/README.md).

## طريقة العمل وحدود الدقة

يستخرج التعرف المحلي توقيتًا تقريبيًا للكلمات، ثم تطابقه الخوارزمية مع النص المرجعي وتقدّر مواقع الكلمات الأخرى. تساعد علامات الترقيم والوقفات وحدود الطول والمدة على تقسيم المقاطع. البرنامج يزامن النص مع الصوت، ولا يترجم بين اللغات. راجع [المعمارية](docs/ARCHITECTURE.md) لمعرفة التنفيذ.

- **راجع التوقيت:** الموسيقى، وتداخل الأصوات، والتكرار، والقص في التسجيل، واختلاف اللهجات قد تقلل جودة المحاذاة. لا نعلن نسبة دقة مستقلة لم تُقَس.
- **استخدم النص المطابق:** تُحفظ الكلمات غير المنطوقة أو المختلفة عن الصوت بتوقيت تقديري. وقد ينتج عن الصمت توقيت منخفض الثقة. صحة صيغة SRT لا تعني صحة توقيته.
- **استخدم low-conf كإشارة للمراجعة:** هو مؤشر داخلي للتطابق، وليس قياسًا مستقلًا لدقة التعرف أو التوقيت.
- **انتظر انتهاء المهمة:** لا يوجد إلغاء أثناء المعالجة حاليًا. يُؤجَّل إغلاق التطبيق حتى انتهاء المهمة، وتتوفر إعادة المحاولة وSave As في حالات الخطأ المدعومة.

العينات تضم نصًا فصيحًا وآخر بصياغة مصرية بصوت عربي اصطناعي. تختبر المسار الكامل والحفاظ على النص، ولا تُعد معيارًا لنطق مصري أصيل. يوضح [سجل التحقق](docs/VERIFICATION.md) الاختبارات المنفذة وما يحتاج تجربة بشرية أو جهازًا محددًا.

## التشغيل من المصدر

استخدم Python 3.11.9 على Windows x64 أو macOS Intel. ابدأ من [دليل التطوير](docs/DEVELOPMENT.md) لإنشاء بيئة افتراضية وتثبيت المتطلبات، ثم جهّز النماذج ومكونات الصوت وفق [دليل البناء](docs/BUILDING.md). تجهيز بيئة التطوير يتطلب تنزيل ملفات من الإنترنت.

بعد تجهيز البيئة والموارد:

```sh
python run.py
python run.py --cli -a examples/msa.wav -t examples/msa.txt -o example.srt --model small
```

الحزم المثبتة تدعم `--cli` أيضًا؛ راجع [أوامر كل نظام](docs/USAGE.md). تعمل فحوص المصدر على Windows وmacOS Intel، وبناء الحزم واختبار النسخ المثبتة خطوات منفصلة للإصدار.

## الخصوصية والتراخيص

تعمل المعالجة داخل جهازك بالنماذج المضمنة. لا يتضمن التطبيق telemetry أو حسابات أو رفعًا للملفات. تنزيل المتطلبات يخص تجهيز بيئة البناء والتطوير. قد تحتوي السجلات المحلية على مسارات أو أجزاء من النص؛ راجعها قبل مشاركتها. [الخصوصية وحل المشكلات](docs/TROUBLESHOOTING.md).

كود التطبيق الأصلي مرخّص **[MIT](LICENSE)، وحقوقه لـElkholasa**. المكتبات والنماذج لها تراخيص منفصلة؛ ترخيص MIT وحده لا يغطي المثبت كله. راجع [الإشعارات](LICENSES.md) و[مصادر المكونات وتعليمات استبدالها](docs/LICENSING.md). العينات الأصلية متاحة وفق [CC0](examples/LICENSE-CC0.txt).

## المساعدة والمساهمة

[الإبلاغ عن مشكلة](https://github.com/elkholasa1111-glitch/ArabicAligner/issues/new?template=bug_report.yml) · [اقتراح ميزة](https://github.com/elkholasa1111-glitch/ArabicAligner/issues/new?template=feature_request.yml) · [سؤال عن الاستخدام](https://github.com/elkholasa1111-glitch/ArabicAligner/issues/new?template=question.yml)

المسؤول عن الصيانة **[Mahmoud Hussein Attay Elsayed](https://github.com/elkholasa1111-glitch)** لصالح **Elkholasa**. راجع [إدارة المشروع](MAINTAINERS.md) و[مصدر النسختين والمساهمات](docs/PROVENANCE.md). نرحب بتحسين الشرح والعينات العربية والاختبارات وتشخيص الأخطاء والبناء؛ البداية من [المساهمة](CONTRIBUTING.md).

[الدعم](SUPPORT.md) · [الأمان](SECURITY.md) · [سجل التغييرات](CHANGELOG.md) · [خطة التطوير](docs/ROADMAP.md)
