import {
  Box,
  Button,
  Flex,
  Heading,
  Text,
  VStack,
  HStack,
  Badge,
  IconButton,
  useToast,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Spinner,
  Alert,
  AlertIcon,
} from '@chakra-ui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import { FiTrash2, FiDownload, FiRefreshCw } from 'react-icons/fi'
import { useDropzone } from 'react-dropzone'
import { format } from 'date-fns'

interface Document {
  id: string
  title: string
  doc_type: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
  chunk_count: number
  metadata: {
    word_count?: number
    file_size?: number
  }
}

const fetchDocuments = async (): Promise<{ documents: Document[]; total: number }> => {
  const response = await fetch('/api/documents/')
  if (!response.ok) {
    throw new Error('Failed to fetch documents')
  }
  return response.json()
}

const uploadDocument = async (file: File): Promise<void> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch('/api/documents/', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to upload document')
  }
}

const deleteDocument = async (id: string): Promise<void> => {
  const response = await fetch(`/api/documents/${id}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error('Failed to delete document')
  }
}

const FileDropzone = ({ onUpload }: { onUpload: (file: File) => void }) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      onUpload(file)
    })
  }, [onUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    multiple: true,
  })

  return (
    <Box
      {...getRootProps()}
      p={8}
      border="2px dashed"
      borderColor={isDragActive ? 'blue.400' : 'gray.300'}
      borderRadius="lg"
      bg={isDragActive ? 'blue.50' : 'gray.50'}
      cursor="pointer"
      transition="all 0.2s"
      _hover={{ borderColor: 'blue.400', bg: 'blue.50' }}
    >
      <input {...getInputProps()} />
      <VStack spacing={2}>
        <Text fontSize="lg" fontWeight="medium" color="gray.600">
          {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
        </Text>
        <Text fontSize="sm" color="gray.400">
          or click to select files
        </Text>
        <Text fontSize="xs" color="gray.400">
          Supported: PDF, DOCX, TXT
        </Text>
      </VStack>
    </Box>
  )
}

const StatusBadge = ({ status }: { status: string }) => {
  const statusColors: Record<string, string> = {
    completed: 'green',
    processing: 'yellow',
    pending: 'gray',
    failed: 'red',
  }

  return (
    <Badge colorScheme={statusColors[status] || 'gray'} textTransform="capitalize">
      {status}
    </Badge>
  )
}

const formatFileSize = (bytes?: number): string => {
  if (!bytes) return 'N/A'
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(1)} KB`
  const mb = kb / 1024
  return `${mb.toFixed(1)} MB`
}

const DocumentManager = () => {
  const toast = useToast()
  const queryClient = useQueryClient()

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['documents'],
    queryFn: fetchDocuments,
    refetchInterval: 5000, // Refetch every 5 seconds to show processing status
  })

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      toast({
        title: 'Document uploaded',
        status: 'success',
        duration: 3000,
      })
    },
    onError: (error: Error) => {
      toast({
        title: 'Upload failed',
        description: error.message,
        status: 'error',
        duration: 5000,
      })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      toast({
        title: 'Document deleted',
        status: 'success',
        duration: 3000,
      })
    },
    onError: (error: Error) => {
      toast({
        title: 'Delete failed',
        description: error.message,
        status: 'error',
        duration: 5000,
      })
    },
  })

  const handleUpload = (file: File) => {
    uploadMutation.mutate(file)
  }

  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      deleteMutation.mutate(id)
    }
  }

  const documents = data?.documents || []

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Box>
          <Heading size="lg">Document Manager</Heading>
          <Text color="gray.500">Upload and manage your documents</Text>
        </Box>
        <Button
          leftIcon={<FiRefreshCw />}
          onClick={() => refetch()}
          isLoading={isLoading}
          variant="outline"
        >
          Refresh
        </Button>
      </Flex>

      <FileDropzone onUpload={handleUpload} />

      {isLoading && documents.length === 0 && (
        <Flex justify="center" py={12}>
          <Spinner size="xl" />
        </Flex>
      )}

      {error && (
        <Alert status="error" mt={6}>
          <AlertIcon />
          {error.message}
        </Alert>
      )}

      {documents.length > 0 && (
        <Box mt={8} bg="white" borderRadius="lg" boxShadow="sm" overflow="hidden">
          <Table variant="simple">
            <Thead bg="gray.50">
              <Tr>
                <Th>Title</Th>
                <Th>Type</Th>
                <Th>Status</Th>
                <Th>Chunks</Th>
                <Th>Size</Th>
                <Th>Uploaded</Th>
                <Th>Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {documents.map((doc) => (
                <Tr key={doc.id}>
                  <Td fontWeight="medium">{doc.title}</Td>
                  <Td>
                    <Badge variant="outline" textTransform="uppercase">
                      {doc.doc_type}
                    </Badge>
                  </Td>
                  <Td>
                    <StatusBadge status={doc.status} />
                  </Td>
                  <Td>{doc.chunk_count}</Td>
                  <Td>{formatFileSize(doc.metadata?.file_size)}</Td>
                  <Td>{format(new Date(doc.created_at), 'MMM d, yyyy')}</Td>
                  <Td>
                    <HStack spacing={2}>
                      <IconButton
                        aria-label="Download"
                        icon={<FiDownload />}
                        size="sm"
                        variant="ghost"
                        as="a"
                        href={`/api/documents/${doc.id}/download`}
                      />
                      <IconButton
                        aria-label="Delete"
                        icon={<FiTrash2 />}
                        size="sm"
                        variant="ghost"
                        colorScheme="red"
                        onClick={() => handleDelete(doc.id)}
                        isLoading={deleteMutation.isPending}
                      />
                    </HStack>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}

      {!isLoading && documents.length === 0 && !error && (
        <Box textAlign="center" py={12}>
          <Text color="gray.500">No documents uploaded yet.</Text>
          <Text color="gray.400" fontSize="sm">
            Use the dropzone above to upload your first document.
          </Text>
        </Box>
      )}
    </Box>
  )
}

export default DocumentManager
