import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:image/image.dart'
    as img; // <-- Added official image compression package
import 'dart:convert';
import 'dart:typed_data';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Structural Registry Workspace',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  final TextEditingController _firstNameController = TextEditingController();
  final TextEditingController _familyNameController = TextEditingController();

  final TextEditingController _addressController = TextEditingController();
  final TextEditingController _birthdayController = TextEditingController();

  String _selectedDocType = "Passport";
  final List<String> _docTypes = [
    "ID Card",
    "Passport",
    "Certificate",
    "Contract",
    "Other",
  ];

  String _message = "Welcome! Please log in or register.";
  bool _isLoading = false;

  bool _isLoggedIn = false;
  bool _isRegisterMode = false;
  String _activeUserEmail = "";

  String? _pickedFileName;
  Uint8List? _pickedFileBytes;

  Map<String, dynamic> _uploadedDocuments = {};

  void _executeLogoutPipeline() {
    setState(() {
      _isLoggedIn = false;
      _activeUserEmail = "";
      _firstNameController.clear();
      _familyNameController.clear();
      _addressController.clear();
      _birthdayController.clear();
      _emailController.clear();
      _passwordController.clear();
      _uploadedDocuments = {};
      _pickedFileBytes = null;
      _pickedFileName = null;
      _message =
          "Session successfully cleared. Welcome! Please log in or register.";
    });
  }

  // ==========================================
  // AUTH ROUTINES
  // ==========================================
  Future<void> handleAuthAction() async {
    String email = _emailController.text.trim();
    String password = _passwordController.text.trim();

    if (email.isEmpty || password.isEmpty) {
      setState(() => _message = "Please fill in email and password fields.");
      return;
    }

    setState(() => _isLoading = true);

    try {
      String endpoint = _isRegisterMode ? 'register' : 'login';
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('https://qridme-backend.onrender.com/$endpoint'),
      );

      request.fields['email'] = email;
      request.fields['password'] = password;

      if (_isRegisterMode) {
        request.fields['first_name'] = _firstNameController.text.trim();
        request.fields['family_name'] = _familyNameController.text.trim();
      }

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          if (!_isRegisterMode) {
            _isLoggedIn = true;
            _activeUserEmail = data['email'];
            _firstNameController.text = data['first_name'] ?? "";
            _familyNameController.text = data['family_name'] ?? "";
            _addressController.text = data['address'] ?? "";
            _birthdayController.text = data['birthday'] ?? "";

            _uploadedDocuments = data['documents'] ?? {};
            _message = "Logged in! Workspace profiles parsed.";
          } else {
            _isRegisterMode = false;
            _message =
                "Account created structure registered! Check email for details.";
          }
        });
      } else {
        final errorData = json.decode(response.body);
        setState(() => _message = errorData['detail'] ?? "Action rejected.");
      }
    } catch (e) {
      setState(() => _message = "Network connector dropped: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // ==========================================
  // DATE PICKER FOR BIRTHDAY
  // ==========================================
  Future<void> _selectBirthdayDate() async {
    DateTime? pickedDate = await showDatePicker(
      context: context,
      initialDate: DateTime(2000),
      firstDate: DateTime(1930),
      lastDate: DateTime.now(),
    );

    if (pickedDate != null) {
      setState(() {
        _birthdayController.text = pickedDate.toString().split(" ")[0];
      });
    }
  }

  // ==========================================
  // UPDATE USER TEXT PROFILE FIELDS
  // ==========================================
  Future<void> updateProfileNames() async {
    String first = _firstNameController.text.trim();
    String family = _familyNameController.text.trim();
    String addr = _addressController.text.trim();
    String bday = _birthdayController.text.trim();

    if (first.isEmpty || family.isEmpty) {
      setState(() => _message = "Names cannot be saved blank.");
      return;
    }

    setState(() => _isLoading = true);
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('https://qridme-backend.onrender.com/update-profile'),
      );
      request.fields['email'] = _activeUserEmail;
      request.fields['first_name'] = first;
      request.fields['family_name'] = family;
      request.fields['address'] = addr;
      request.fields['birthday'] = bday;

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _firstNameController.text = data['first_name'];
          _familyNameController.text = data['family_name'];
          _addressController.text = data['address'];
          _birthdayController.text = data['birthday'];
          _message = "Identity variables updated successfully inside database!";
        });
      }
    } catch (e) {
      setState(() => _message = "Update operation error: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // ==========================================
  // EMBED WORKSPACE PROFILE TO QR
  // ==========================================
  void generateProfileQrCode() {
    String first = _firstNameController.text.trim();
    String family = _familyNameController.text.trim();
    String addr = _addressController.text.trim();
    String bday = _birthdayController.text.trim();

    StringBuffer qrContentBuffer = StringBuffer();
    qrContentBuffer.writeln("=== USER PROFILE RECORD ===");
    qrContentBuffer.writeln("Full Name: $first $family");
    qrContentBuffer.writeln("Email: $_activeUserEmail");
    qrContentBuffer.writeln("Address: ${addr.isEmpty ? 'Not Provided' : addr}");
    qrContentBuffer.writeln(
      "Birthday: ${bday.isEmpty ? 'Not Provided' : bday}",
    );

    qrContentBuffer.writeln("\n=== ATTACHED DOCUMENTS ===");
    if (_uploadedDocuments.isEmpty) {
      qrContentBuffer.writeln("No documents uploaded yet.");
    } else {
      _uploadedDocuments.forEach((key, value) {
        String docName = value['file_name'] ?? "Unknown File";
        String docType = value['document_type'] ?? "Other";
        String linkUrl = value['download_url'] ?? "";
        qrContentBuffer.writeln("- [$docType] $docName: $linkUrl");
      });
    }

    String finalQrDataString = qrContentBuffer.toString();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.qr_code_2, color: Colors.blueAccent, size: 28),
            SizedBox(width: 10),
            Text("Generated Profile QR Code"),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              "Scan this QR code to access full registry text details and direct database download URLs instantly.",
              style: TextStyle(fontSize: 12, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: SizedBox(
                width: 220,
                height: 220,
                child: QrImageView(
                  data: finalQrDataString,
                  version: QrVersions.auto,
                  size: 220.0,
                  gapless: false,
                  errorStateBuilder: (cxt, err) {
                    return const Center(
                      child: Text(
                        "Data payload is too heavy to compress to QR. Remove some files and try again.",
                      ),
                    );
                  },
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              "Embedded Data Payload Size: ${finalQrDataString.length} characters",
              style: const TextStyle(fontSize: 10, fontStyle: FontStyle.italic),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Close Window"),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // FILE SELECTION WITH SMART LIMITS & COMPRESSION
  // ==========================================
  Future<void> pickFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.any,
        withData: true,
      );

      if (result != null && result.files.isNotEmpty) {
        PlatformFile selectedFile = result.files.first;
        Uint8List? rawBytes = selectedFile.bytes;
        String fileName = selectedFile.name;

        if (rawBytes == null) return;

        // 🛡️ SECURITY GUARD: 5MB File Size Limit Check
        // 5MB = 5 * 1024 * 1024 bytes = 5,242,880 bytes
        const int hardLimit = 5 * 1024 * 1024;
        if (rawBytes.length > hardLimit) {
          setState(() {
            _message =
                "❌ Upload Blocked: '${selectedFile.name}' is larger than 5MB limit. Please select a smaller file.";
            _pickedFileName = null;
            _pickedFileBytes = null;
          });
          return;
        }

        String ext = fileName.split('.').last.toLowerCase();
        bool isImage = ext == 'jpg' || ext == 'jpeg' || ext == 'png';

        // 📉 PERFORMANCE ENGINE: Auto-Compress Large Images (> 1MB)
        if (isImage && rawBytes.length > 1 * 1024 * 1024) {
          setState(
            () => _message =
                "⚡ Heavy image detected. Compressing automatically for speed...",
          );

          // Decode image in a separate asynchronous task structure simulation
          img.Image? decodedImg = img.decodeImage(rawBytes);
          if (decodedImg != null) {
            // Resize image to max 1200px width/height maintaining aspect ratio
            img.Image resizedImg = img.copyResize(
              decodedImg,
              width: decodedImg.width > 1200 ? 1200 : null,
              height: decodedImg.height > 1200 ? 1200 : null,
            );

            // Re-encode image to standard JPEG at 80% compression quality
            Uint8List compressedBytes = Uint8List.fromList(
              img.encodeJpg(resizedImg, quality: 80),
            );

            print(
              "Compression Metrics: Original: ${rawBytes.length} bytes -> Compressed: ${compressedBytes.length} bytes",
            );
            rawBytes = compressedBytes;
            fileName = "${fileName.split('.').first}_optimized.jpg";
          }
        }

        setState(() {
          _pickedFileName = fileName;
          _pickedFileBytes = rawBytes;
          _message =
              "Attached successfully: $_pickedFileName (${(rawBytes!.length / 1024).toStringAsFixed(1)} KB)";
        });
      }
    } catch (e) {
      setState(() => _message = "Picker broke: $e");
    }
  }

  // ==========================================
  // UPLOAD & FILE DELETION (Kept Untouched)
  // ==========================================
  Future<void> refreshDocumentsList() async {
    try {
      final response = await http.get(
        Uri.parse(
          'https://qridme-backend.onrender.com/get-documents?email=$_activeUserEmail',
        ),
      );
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _uploadedDocuments = data['documents'] ?? {};
        });
      }
    } catch (e) {
      print("Error reloading items tree: $e");
    }
  }

  Future<void> saveFileToUserTree() async {
    if (_pickedFileBytes == null || _pickedFileName == null) return;
    setState(() => _isLoading = true);

    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('https://qridme-backend.onrender.com/upload'),
      );
      request.fields['email'] = _activeUserEmail;
      request.fields['document_type'] = _selectedDocType;
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          _pickedFileBytes!,
          filename: _pickedFileName!,
        ),
      );

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        setState(() {
          _pickedFileBytes = null;
          _pickedFileName = null;
          _message = "File saved perfectly to Firebase Storage bucket!";
        });
        await refreshDocumentsList();
      }
    } catch (e) {
      setState(() => _message = "Upload channel boundary broke: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> deleteDocument(String docId, String downloadUrl) async {
    bool confirmDelete =
        await showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Row(
              children: [
                Icon(Icons.warning_amber_rounded, color: Colors.red),
                SizedBox(width: 10),
                Text("Delete Document?"),
              ],
            ),
            content: const Text(
              "Are you sure you want to delete this document permanently?",
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text("Cancel"),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context, true),
                style: TextButton.styleFrom(foregroundColor: Colors.red),
                child: const Text("Delete"),
              ),
            ],
          ),
        ) ??
        false;

    if (!confirmDelete) return;
    setState(() => _isLoading = true);
    try {
      final response = await http.post(
        Uri.parse('https://qridme-backend.onrender.com/delete-document'),
        headers: {"Content-Type": "application/json"},
        body: json.encode({
          'email': _activeUserEmail,
          'doc_id': docId,
          'download_url': downloadUrl,
        }),
      );

      if (response.statusCode == 200) {
        setState(() => _message = "Document completely purged.");
        await refreshDocumentsList();
      }
    } catch (e) {
      setState(() => _message = "Delete error: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> deleteEntireAccount() async {
    final TextEditingController confirmPasswordController =
        TextEditingController();
    bool confirmDelete =
        await showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Row(
              children: [
                Icon(Icons.dangerous, color: Colors.red),
                SizedBox(width: 8),
                Text("Delete Account Permanently?"),
              ],
            ),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  "This action purges all profile records permanently. Enter password to confirm.",
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: confirmPasswordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: "Confirm Password",
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text("Cancel"),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context, true),
                style: TextButton.styleFrom(foregroundColor: Colors.red),
                child: const Text("Delete Everything"),
              ),
            ],
          ),
        ) ??
        false;

    if (!confirmDelete) return;
    if (confirmPasswordController.text.trim().isEmpty) return;

    setState(() => _isLoading = true);
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('https://qridme-backend.onrender.com/delete-account'),
      );
      request.fields['email'] = _activeUserEmail;
      request.fields['password'] = confirmPasswordController.text.trim();

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        _executeLogoutPipeline();
        setState(() => _message = "Your account has been deleted completely.");
      }
    } catch (e) {
      setState(() => _message = "Account deletion error: $e");
    } finally {
      confirmPasswordController.dispose();
      setState(() => _isLoading = false);
    }
  }

  void _openDocumentPreview(String name, String type, String url) async {
    String fileNameLower = name.toLowerCase();
    if (fileNameLower.endsWith('.pdf')) {
      setState(() => _message = "Opening PDF preview in a new tab...");
      await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
      return;
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("$type: $name"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (fileNameLower.endsWith('.jpg') ||
                fileNameLower.endsWith('.png') ||
                fileNameLower.endsWith('.jpeg'))
              Container(
                constraints: const BoxConstraints(maxHeight: 300),
                child: Image.network(url),
              )
            else
              const Text("No preview layout available."),
            const SizedBox(height: 16),
            SelectableText(
              url,
              style: const TextStyle(fontSize: 12, color: Colors.blue),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Close"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: ShaderMask(
          shaderCallback: (bounds) => const LinearGradient(
            colors: [
              Colors.red,
              Colors.orange,
              Colors.yellow,
              Colors.green,
              Colors.blue,
              Colors.indigo,
              Colors.purple,
            ],
            tileMode: TileMode.clamp,
          ).createShader(Rect.fromLTWH(0, 0, bounds.width, bounds.height)),
          child: Text(
            _isLoggedIn
                ? 'QRIDME Scan. Identify. Connect.'
                : 'QRIDME Identity Registry Gateway',
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight
                  .w900, // <-- FIXED: Changed from .black to .w900 for ultra-thick styling
              fontSize: 20,
            ),
          ),
        ),
        actions: _isLoggedIn
            ? [
                IconButton(
                  icon: const Icon(Icons.logout),
                  onPressed: _executeLogoutPipeline,
                ),
              ]
            : null,
      ),
      body: Center(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 460),
              child: Column(
                children: [
                  if (!_isLoggedIn) ...[
                    Card(
                      elevation: 4,
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          children: [
                            Text(
                              _isRegisterMode
                                  ? "Register Profile"
                                  : "Portal Access Login",
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 18,
                              ),
                            ),
                            const SizedBox(height: 20),
                            if (_isRegisterMode) ...[
                              TextField(
                                controller: _firstNameController,
                                decoration: const InputDecoration(
                                  labelText: "First Name",
                                  border: OutlineInputBorder(),
                                ),
                              ),
                              const SizedBox(height: 14),
                              TextField(
                                controller: _familyNameController,
                                decoration: const InputDecoration(
                                  labelText: "Family Name",
                                  border: OutlineInputBorder(),
                                ),
                              ),
                              const SizedBox(height: 14),
                            ],
                            TextField(
                              controller: _emailController,
                              keyboardType: TextInputType.emailAddress,
                              decoration: const InputDecoration(
                                labelText: "Email Address",
                                border: OutlineInputBorder(),
                              ),
                            ),
                            const SizedBox(height: 14),
                            TextField(
                              controller: _passwordController,
                              obscureText: true,
                              decoration: const InputDecoration(
                                labelText: "Password",
                                border: OutlineInputBorder(),
                              ),
                            ),
                            const SizedBox(height: 20),
                            SizedBox(
                              width: double.infinity,
                              height: 46,
                              child: ElevatedButton(
                                onPressed: handleAuthAction,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.blue.shade800,
                                  foregroundColor: Colors.white,
                                ),
                                child: Text(
                                  _isRegisterMode ? "Create Account" : "Log In",
                                ),
                              ),
                            ),
                            TextButton(
                              onPressed: () => setState(
                                () => _isRegisterMode = !_isRegisterMode,
                              ),
                              child: Text(
                                _isRegisterMode
                                    ? "Existing profile? Log In"
                                    : "Register new node",
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ] else ...[
                    Center(
                      child: Text(
                        "Workspace: $_activeUserEmail",
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                          color: Colors.blue,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    Card(
                      elevation: 3,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              "Edit Identity Profile Parameters",
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(height: 16),
                            TextField(
                              controller: _firstNameController,
                              decoration: const InputDecoration(
                                labelText: "First Name",
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.badge),
                              ),
                            ),
                            const SizedBox(height: 12),
                            TextField(
                              controller: _familyNameController,
                              decoration: const InputDecoration(
                                labelText: "Family Name",
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.group),
                              ),
                            ),
                            const SizedBox(height: 12),
                            TextField(
                              controller: _addressController,
                              decoration: const InputDecoration(
                                labelText: "Address",
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.home),
                              ),
                            ),
                            const SizedBox(height: 12),
                            TextField(
                              controller: _birthdayController,
                              readOnly: true,
                              onTap: _selectBirthdayDate,
                              decoration: const InputDecoration(
                                labelText: "Birthday",
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.cake),
                              ),
                            ),
                            const SizedBox(height: 16),
                            SizedBox(
                              width: double.infinity,
                              height: 44,
                              child: ElevatedButton.icon(
                                onPressed: updateProfileNames,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.blue.shade700,
                                  foregroundColor: Colors.white,
                                ),
                                icon: const Icon(Icons.save_as),
                                label: const Text(
                                  "Update Profile Names",
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                ),
                              ),
                            ),
                            const SizedBox(height: 10),
                            SizedBox(
                              width: double.infinity,
                              height: 44,
                              child: ElevatedButton.icon(
                                onPressed: generateProfileQrCode,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.indigo.shade600,
                                  foregroundColor: Colors.white,
                                ),
                                icon: const Icon(Icons.qr_code),
                                label: const Text(
                                  "Generate Profile QR Code",
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),

                    Card(
                      elevation: 3,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              "Upload Documents to Storage Node",
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(height: 16),
                            DropdownButtonFormField<String>(
                              value: _selectedDocType,
                              decoration: const InputDecoration(
                                border: OutlineInputBorder(),
                                labelText: "Document Property Mapping Type",
                              ),
                              items: _docTypes
                                  .map(
                                    (type) => DropdownMenuItem(
                                      value: type,
                                      child: Text(type),
                                    ),
                                  )
                                  .toList(),
                              onChanged: (val) =>
                                  setState(() => _selectedDocType = val!),
                            ),
                            const SizedBox(height: 16),
                            SizedBox(
                              width: double.infinity,
                              child: OutlinedButton.icon(
                                onPressed: pickFile,
                                icon: const Icon(Icons.attach_file),
                                label: Text(
                                  _pickedFileName != null
                                      ? "Replace Selected File"
                                      : "Browse Document Source",
                                ),
                              ),
                            ),
                            if (_pickedFileName != null) ...[
                              const SizedBox(height: 8),
                              Text(
                                "Attached: $_pickedFileName",
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Colors.green,
                                ),
                              ),
                            ],
                            const SizedBox(height: 18),
                            SizedBox(
                              width: double.infinity,
                              height: 44,
                              child: ElevatedButton(
                                onPressed: saveFileToUserTree,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.green.shade700,
                                  foregroundColor: Colors.white,
                                ),
                                child: const Text(
                                  "Save Document to Tree Node",
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),

                    Card(
                      elevation: 3,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              "Your Stored Profile Documents",
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(height: 12),
                            _uploadedDocuments.isEmpty
                                ? const Padding(
                                    padding: EdgeInsets.symmetric(vertical: 20),
                                    child: Center(
                                      child: Text(
                                        "No documents saved yet.",
                                        style: TextStyle(
                                          color: Colors.grey,
                                          fontSize: 13,
                                        ),
                                      ),
                                    ),
                                  )
                                : ListView.builder(
                                    shrinkWrap: true,
                                    physics:
                                        const NeverScrollableScrollPhysics(),
                                    itemCount: _uploadedDocuments.length,
                                    itemBuilder: (context, index) {
                                      String key = _uploadedDocuments.keys
                                          .elementAt(index);
                                      var docItem = _uploadedDocuments[key];
                                      String docName =
                                          docItem['file_name'] ??
                                          "Unknown File";
                                      String docType =
                                          docItem['document_type'] ?? "Other";
                                      String downloadUrl =
                                          docItem['download_url'] ?? "";

                                      return Card(
                                        color: Colors.grey.shade50,
                                        margin: const EdgeInsets.symmetric(
                                          vertical: 6,
                                        ),
                                        child: Row(
                                          children: [
                                            Expanded(
                                              child: ListTile(
                                                leading: const Icon(
                                                  Icons.file_present,
                                                  color: Colors.blueAccent,
                                                ),
                                                title: Text(
                                                  docName,
                                                  style: const TextStyle(
                                                    fontSize: 13,
                                                    fontWeight: FontWeight.bold,
                                                    decoration: TextDecoration
                                                        .underline,
                                                    color: Colors.indigo,
                                                  ),
                                                ),
                                                subtitle: Text(
                                                  "Type: $docType",
                                                  style: const TextStyle(
                                                    fontSize: 11,
                                                  ),
                                                ),
                                                onTap: () =>
                                                    _openDocumentPreview(
                                                      docName,
                                                      docType,
                                                      downloadUrl,
                                                    ),
                                              ),
                                            ),
                                            IconButton(
                                              icon: const Icon(
                                                Icons.delete_forever,
                                                color: Colors.red,
                                              ),
                                              onPressed: () => deleteDocument(
                                                key,
                                                downloadUrl,
                                              ),
                                              tooltip:
                                                  "Delete document permanently",
                                            ),
                                            const SizedBox(width: 8),
                                          ],
                                        ),
                                      );
                                    },
                                  ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    SizedBox(
                      width: double.infinity,
                      height: 46,
                      child: ElevatedButton.icon(
                        onPressed: _executeLogoutPipeline,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.grey.shade700,
                          foregroundColor: Colors.white,
                        ),
                        icon: const Icon(Icons.exit_to_app),
                        label: const Text(
                          "Log Out of Workspace",
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      height: 46,
                      child: OutlinedButton.icon(
                        onPressed: deleteEntireAccount,
                        style: OutlinedButton.styleFrom(
                          side: const BorderSide(color: Colors.red),
                          foregroundColor: Colors.red,
                        ),
                        icon: const Icon(Icons.person_remove_alt_1),
                        label: const Text(
                          "Delete Account Entirely",
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 24),
                  _isLoading
                      ? const CircularProgressIndicator()
                      : Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.grey.shade100,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.grey.shade300),
                          ),
                          child: SelectableText(
                            _message,
                            textAlign: TextAlign.center,
                            style: const TextStyle(fontSize: 13),
                          ),
                        ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
