#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <windows.h>
#include <pthread.h>
#include <regex>
#include <algorithm>
#include <cstring>

class NoteObject
{
public:
    std::string file_name;
    std::string name;
    std::string id;
    std::string parent_id;
    std::string is_shared;
    std::string encryption_applied;
    std::string encryption_cipher_text;
    std::string updated_time;
    std::string user_updated_time;
    std::string created_time;
    std::string user_created_time;
    std::string is_conflict;
    std::string latitude;
    std::string longitude;
    std::string altitude;
    std::string author;
    std::string source_url;
    std::string is_todo;
    std::string todo_due;
    std::string todo_completed;
    std::string source;
    std::string source_application;
    std::string application_data;
    long long order;
    std::string markup_language;
    std::string type_;

    NoteObject() : order(0) {}
};

struct ThreadData
{
    std::vector<std::string> files;
    std::vector<NoteObject> *notes;
    size_t start_idx;
    size_t end_idx;
    pthread_mutex_t *mutex;
};

std::string trim(const std::string &str)
{
    size_t first = str.find_first_not_of(' ');
    if (first == std::string::npos)
        return "";
    size_t last = str.find_last_not_of(' ');
    return str.substr(first, (last - first + 1));
}

void parseMetadata(const std::string &line, NoteObject &note)
{
    size_t colon_pos = line.find(':');
    if (colon_pos == std::string::npos)
        return;

    std::string key = trim(line.substr(0, colon_pos));
    std::string value = trim(line.substr(colon_pos + 1));

    if (key == "id")
        note.id = value;
    else if (key == "parent_id")
        note.parent_id = value;
    else if (key == "is_shared")
        note.is_shared = value;
    else if (key == "encryption_applied")
        note.encryption_applied = value;
    else if (key == "encryption_cipher_text")
        note.encryption_cipher_text = value;
    else if (key == "updated_time")
        note.updated_time = value;
    else if (key == "user_updated_time")
        note.user_updated_time = value;
    else if (key == "created_time")
        note.created_time = value;
    else if (key == "user_created_time")
        note.user_created_time = value;
    else if (key == "is_conflict")
        note.is_conflict = value;
    else if (key == "latitude")
        note.latitude = value;
    else if (key == "longitude")
        note.longitude = value;
    else if (key == "altitude")
        note.altitude = value;
    else if (key == "author")
        note.author = value;
    else if (key == "source_url")
        note.source_url = value;
    else if (key == "is_todo")
        note.is_todo = value;
    else if (key == "todo_due")
        note.todo_due = value;
    else if (key == "todo_completed")
        note.todo_completed = value;
    else if (key == "source")
        note.source = value;
    else if (key == "source_application")
        note.source_application = value;
    else if (key == "application_data")
        note.application_data = value;
    else if (key == "order")
        note.order = std::stoll(value);
    else if (key == "markup_language")
        note.markup_language = value;
    else if (key == "type_")
        note.type_ = value;
}

std::vector<std::string> findMarkdownFiles(const std::string &directory)
{
    std::vector<std::string> md_files;

    // Read from file list
    std::ifstream file_list("file_list.txt");
    if (!file_list.is_open())
    {
        std::cerr << "Error: Could not open file_list.txt" << std::endl;
        return md_files;
    }

    std::string filename;
    int file_count = 0;
    while (std::getline(file_list, filename))
    { // Process all files
        // Remove any trailing whitespace/newlines
        filename.erase(filename.find_last_not_of(" \t\n\r\f\v") + 1);
        if (!filename.empty())
        {
            md_files.push_back(filename); // Just use filename directly
            std::cout << "Found MD file: " << filename << std::endl;
            file_count++;
        }
    }
    file_list.close();

    return md_files;
}

std::string getFilename(const std::string &filepath)
{
    size_t pos = filepath.find_last_of("\\");
    if (pos == std::string::npos)
        pos = filepath.find_last_of("/");
    if (pos == std::string::npos)
        return filepath;
    return filepath.substr(pos + 1);
}

NoteObject parseMarkdownFile(const std::string &filepath)
{
    NoteObject note;
    note.file_name = getFilename(filepath);

    std::ifstream file(filepath);
    if (!file.is_open())
    {
        std::cerr << "Error opening file: " << filepath << std::endl;
        return note;
    }

    std::string line;
    std::vector<std::string> lines;

    // Read all lines
    while (std::getline(file, line))
    {
        lines.push_back(line);
    }
    file.close();

    if (lines.empty())
        return note;

    // First line is the name
    note.name = trim(lines[0]);

    // Parse metadata from the end - look for "type_:" first, then parse upward to "id:"
    bool in_metadata = false;
    for (int i = lines.size() - 1; i >= 0; i--)
    {
        std::string trimmed_line = trim(lines[i]);

        // Start metadata parsing when we find "type_:" at the end
        if (!in_metadata && trimmed_line.find("type_:") == 0)
        {
            in_metadata = true;
            parseMetadata(trimmed_line, note);
        }
        // Continue parsing if we're in metadata and the line has metadata format
        else if (in_metadata && trimmed_line.find(':') != std::string::npos)
        {
            parseMetadata(trimmed_line, note);
            // Stop when we reach the id: line (beginning of metadata)
            if (trimmed_line.find("id:") == 0)
            {
                break;
            }
        }
        // Skip empty lines in metadata
        else if (in_metadata && trimmed_line.empty())
        {
            continue;
        }
        // End of metadata section (reached content above metadata)
        else if (in_metadata)
        {
            break;
        }
    }

    return note;
}

void *processFiles(void *arg)
{
    ThreadData *data = static_cast<ThreadData *>(arg);

    for (size_t i = data->start_idx; i < data->end_idx; i++)
    {
        NoteObject note = parseMarkdownFile(data->files[i]);

        pthread_mutex_lock(data->mutex);
        data->notes->push_back(note);
        pthread_mutex_unlock(data->mutex);
    }

    return nullptr;
}

void buildTree(const std::vector<NoteObject> &notes, const std::string &parent_id,
               int depth, std::ofstream &output, const std::string &mode)
{

    // Find children of current parent, sorted by order (descending)
    std::vector<const NoteObject *> children;
    for (const auto &note : notes)
    {
        if (note.parent_id == parent_id)
        {
            children.push_back(&note);
        }
    }

    // Sort by order descending
    std::sort(children.begin(), children.end(),
              [](const NoteObject *a, const NoteObject *b)
              {
                  return a->order > b->order;
              });

    for (size_t i = 0; i < children.size(); i++)
    {
        const NoteObject *child = children[i];

        // Print tree structure
        for (int j = 0; j < depth; j++)
        {
            output << "│   ";
        }

        if (i == children.size() - 1)
        {
            output << "└── ";
        }
        else
        {
            output << "├── ";
        }

        // Print according to mode
        if (mode == "file_name")
        {
            output << child->file_name << std::endl;
        }
        else if (mode == "name")
        {
            output << child->name << " {" << child->order << ";" << child->file_name << "} " << std::endl;
        }
        else if (mode == "id")
        {
            output << child->id << std::endl;
        }

        // Recursively build tree for this child
        buildTree(notes, child->id, depth + 1, output, mode);
    }
}

int main()
{
    const std::string directory = "."; // Use current directory approach
    std::vector<std::string> md_files;
    std::vector<NoteObject> notes;

    // Find all .md files
    std::cout << "Looking for files in directory: " << directory << std::endl;
    md_files = findMarkdownFiles(directory);

    std::cout << "Found " << md_files.size() << " markdown files." << std::endl;

    // Use pthread to process files
    const int num_threads = 4;
    pthread_t threads[num_threads];
    ThreadData thread_data[num_threads];
    pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

    size_t files_per_thread = md_files.size() / num_threads;
    size_t remaining_files = md_files.size() % num_threads;

    for (int i = 0; i < num_threads; i++)
    {
        thread_data[i].files = md_files;
        thread_data[i].notes = &notes;
        thread_data[i].start_idx = i * files_per_thread;
        thread_data[i].end_idx = (i + 1) * files_per_thread;
        if (i == num_threads - 1)
        {
            thread_data[i].end_idx += remaining_files;
        }
        thread_data[i].mutex = &mutex;

        pthread_create(&threads[i], nullptr, processFiles, &thread_data[i]);
    }

    // Wait for all threads to complete
    for (int i = 0; i < num_threads; i++)
    {
        pthread_join(threads[i], nullptr);
    }

    pthread_mutex_destroy(&mutex);

    std::cout << "Processed " << notes.size() << " notes." << std::endl;

    // Generate three versions of tree.txt
    std::vector<std::string> modes = {"file_name", "name", "id"};

    for (const std::string &mode : modes)
    {
        std::string filename = "tree_" + mode + ".txt";
        std::ofstream output(filename);

        if (!output.is_open())
        {
            std::cerr << "Error creating output file: " << filename << std::endl;
            continue;
        }

        output << "Tree structure (" << mode << "):" << std::endl;
        output << "└── Root" << std::endl;

        // Find root nodes (those with empty parent_id or parent_id not found in the set)
        std::map<std::string, bool> id_exists;
        for (const auto &note : notes)
        {
            id_exists[note.id] = true;
        }

        std::vector<std::string> root_ids;
        for (const auto &note : notes)
        {
            if (note.parent_id.empty() || id_exists.find(note.parent_id) == id_exists.end())
            {
                root_ids.push_back(note.id);
            }
        }

        std::cout << "Total root nodes: " << root_ids.size() << std::endl;

        // Remove duplicates
        std::sort(root_ids.begin(), root_ids.end());
        root_ids.erase(std::unique(root_ids.begin(), root_ids.end()), root_ids.end());

        // Build tree for each root
        for (const std::string &root_id : root_ids)
        {
            buildTree(notes, root_id, 1, output, mode);
        }

        output.close();
        std::cout << "Generated " << filename << std::endl;
    }

    return 0;
}